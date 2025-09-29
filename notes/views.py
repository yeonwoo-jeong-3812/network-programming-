from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods

from .models import Note, Subject, Summary, Quiz
from . import ai

# note_list 함수 추가
def note_list(request):
    # 데이터베이스에 있는 모든 Note 객체를 가져옵니다.
    notes = Note.objects.all()
    # notes라는 이름으로 템플릿에 note 객체 목록을 전달합니다.
    return render(request, 'notes/note_list.html', {'notes': notes})

def note_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        author = User.objects.first() 
        subject, created = Subject.objects.get_or_create(name='네트워크 프로그래밍')
        
        Note.objects.create(
            title=title,
            content=content,
            author=author,
            subject=subject
        )
        
        # 이제 에러가 나던 '/'가 아니라, 우리가 만든 목록 페이지로 이동시킵니다.
        return redirect('note_list') # 'note_list'라는 별명을 가진 URL로 이동!

    return render(request, 'notes/note_create.html')


@require_http_methods(["GET", "POST"])
def upload_pdf(request):
    """Upload a PDF and create a Note with extracted text."""
    if request.method == 'POST':
        file = request.FILES.get('pdf')
        title = request.POST.get('title') or (file.name if file else 'PDF 노트')
        if not file:
            messages.error(request, 'PDF 파일을 선택해주세요.')
            return render(request, 'notes/upload_pdf.html')
        try:
            # 임시로 Note를 만들며 파일을 저장하기 위해 author/subject 준비
            author = User.objects.first()
            subject_name = (request.POST.get('subject') or '').strip() or '네트워크 프로그래밍'
            subject, _ = Subject.objects.get_or_create(name=subject_name)

            note = Note(author=author, subject=subject, title=title)
            note.pdf_file = file
            note.content = ''  # 일단 비워두고, 저장 후 경로로 텍스트 추출
            note.save()

            # 파일 경로 기반 텍스트 추출
            extracted = ai.extract_text_from_pdf(note.pdf_file.path)
            note.content = extracted or ''
            note.save()

            messages.success(request, 'PDF 업로드 및 텍스트 추출을 완료했습니다.')
            return redirect('note_detail', note_id=note.id)
        except Exception as e:
            messages.error(request, f'업로드 중 오류: {e}')
    return render(request, 'notes/upload_pdf.html')


def note_detail(request, note_id: int):
    note = get_object_or_404(Note, id=note_id)
    summary = Summary.objects.filter(note=note).first()
    quizzes = Quiz.objects.filter(summary=summary) if summary else []
    return render(request, 'notes/note_detail.html', {
        'note': note,
        'summary': summary,
        'quizzes': quizzes,
    })


def subject_list(request):
    subjects = Subject.objects.all().order_by('name')
    return render(request, 'notes/subject_list.html', {
        'subjects': subjects,
    })


def subject_detail(request, subject_id: int):
    subject = get_object_or_404(Subject, id=subject_id)
    notes = Note.objects.filter(subject=subject).order_by('-created_at')
    summaries = Summary.objects.filter(note__subject=subject).select_related('note')
    return render(request, 'notes/subject_detail.html', {
        'subject': subject,
        'notes': notes,
        'summaries': summaries,
    })


@require_http_methods(["POST"])
def summarize_note(request, note_id: int):
    note = get_object_or_404(Note, id=note_id)
    try:
        if not note.content:
            messages.error(request, '노트 내용이 비어있어 요약할 수 없습니다.')
            return redirect('note_detail', note_id=note.id)
        summary_text = ai.summarize_text(note.content, language='ko')
        summary, _ = Summary.objects.get_or_create(note=note)
        summary.content = summary_text
        summary.save()
        messages.success(request, 'AI 요약을 생성했습니다.')
    except Exception as e:
        messages.error(request, f'요약 생성 중 오류: {e}')
    return redirect('note_detail', note_id=note.id)


@require_http_methods(["POST"]) 
def generate_quiz(request, note_id: int):
    note = get_object_or_404(Note, id=note_id)
    summary = Summary.objects.filter(note=note).first()
    if not summary:
        messages.error(request, '먼저 요약을 생성해주세요.')
        return redirect('note_detail', note_id=note.id)
    try:
        # 기본 5문제 생성, 필요시 폼에서 수 변경 가능
        items = ai.generate_ox_quiz(summary.content, num_questions=5, language='ko')
        created = 0
        for it in items:
            q_text = it.get('question', '').strip()
            if not q_text:
                continue
            Quiz.objects.create(
                summary=summary,
                question=q_text,
                answer=bool(it.get('answer', False)),
                explanation=it.get('explanation', ''),
            )
            created += 1
        if created:
            messages.success(request, f'OX 퀴즈 {created}개를 생성했습니다.')
        else:
            messages.warning(request, '퀴즈를 생성하지 못했습니다. 요약 내용을 확인해주세요.')
    except Exception as e:
        messages.error(request, f'퀴즈 생성 중 오류: {e}')
    return redirect('note_detail', note_id=note.id)

@require_http_methods(["POST"])
def grade_quiz(request, note_id: int):
    note = get_object_or_404(Note, id=note_id)
    summary = Summary.objects.filter(note=note).first()
    if not summary:
        messages.error(request, '먼저 요약을 생성해주세요.')
        return redirect('note_detail', note_id=note.id)

    quizzes = list(Quiz.objects.filter(summary=summary))
    if not quizzes:
        messages.warning(request, '채점할 퀴즈가 없습니다. 먼저 퀴즈를 생성해주세요.')
        return redirect('note_detail', note_id=note.id)

    results = []
    correct_count = 0
    total = len(quizzes)

    for q in quizzes:
        key = f"answer_{q.id}"
        raw = request.POST.get(key, "")
        # 허용 값: "true"/"false"/"O"/"X"
        if raw.lower() in ("o", "true", "t"):
            user_answer = True
        elif raw.lower() in ("x", "false", "f"):
            user_answer = False
        else:
            user_answer = None

        is_correct = (user_answer is not None and user_answer == q.answer)
        if is_correct:
            correct_count += 1
        results.append({
            "id": q.id,
            "question": q.question,
            "correct_answer": q.answer,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "explanation": q.explanation or "",
        })

    score = correct_count
    messages.info(request, f'채점 결과: {score}/{total} 문제 정답')

    return render(request, 'notes/note_detail.html', {
        'note': note,
        'summary': summary,
        'quizzes': quizzes,
        'graded': True,
        'score': score,
        'total': total,
        'results': results,
    })