from django.urls import path
from . import views

urlpatterns = [
    # 첫 화면: 과목 목록
    path('', views.subject_list, name='subject_list'),
    
    # 'notes/create/' 로 접속했을 때 note_create 함수를 실행, 이 URL의 별명은 'note_create'
    path('create/', views.note_create, name='note_create'),

    # PDF 업로드 페이지
    path('upload/', views.upload_pdf, name='upload_pdf'),

    # 과목별 보기(명시적 경로)
    path('subjects/', views.subject_list, name='subject_list_explicit'),
    path('subjects/<int:subject_id>/', views.subject_detail, name='subject_detail'),

    # 노트 상세/요약/퀴즈 생성
    path('note/<int:note_id>/', views.note_detail, name='note_detail'),
    path('note/<int:note_id>/summarize/', views.summarize_note, name='summarize_note'),
    path('note/<int:note_id>/quiz/', views.generate_quiz, name='generate_quiz'),
    path('note/<int:note_id>/quiz/grade/', views.grade_quiz, name='grade_quiz'),
]