from django.urls import path
from . import views

urlpatterns = [
    # 'notes/' 로 접속했을 때 note_list 함수를 실행, 이 URL의 별명은 'note_list'
    path('', views.note_list, name='note_list'),
    
    # 'notes/create/' 로 접속했을 때 note_create 함수를 실행, 이 URL의 별명은 'note_create'
    path('create/', views.note_create, name='note_create'),

    # PDF 업로드 페이지
    path('upload/', views.upload_pdf, name='upload_pdf'),

    # 노트 상세/요약/퀴즈 생성
    path('note/<int:note_id>/', views.note_detail, name='note_detail'),
    path('note/<int:note_id>/summarize/', views.summarize_note, name='summarize_note'),
    path('note/<int:note_id>/quiz/', views.generate_quiz, name='generate_quiz'),
]