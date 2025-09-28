# notes/admin.py

from django.contrib import admin
from .models import Subject, Note, Summary, Quiz

admin.site.register(Subject)
admin.site.register(Note)
admin.site.register(Summary)
admin.site.register(Quiz)
