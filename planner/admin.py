from django.contrib import admin
from .models import UserProject, ProjectAnalysis, ProjectChatMessage

admin.site.register(UserProject)
admin.site.register(ProjectAnalysis)
admin.site.register(ProjectChatMessage)
