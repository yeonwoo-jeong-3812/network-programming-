from django.db import models
from django.contrib.auth.models import User

# 과목 모델
class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# 필기 원본 모델
class Note(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    pdf_file = models.FileField(upload_to='notes/pdfs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# AI 요약 모델
class Summary(models.Model):
    note = models.OneToOneField(Note, on_delete=models.CASCADE)
    content = models.TextField()

# OX 퀴즈 모델
class Quiz(models.Model):
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    answer = models.BooleanField(help_text="정답이면 True(체크), 오답이면 False(체크 해제)")
    explanation = models.TextField(blank=True) # 근거는 비어있을 수도 있음

    def __str__(self):
        return self.question