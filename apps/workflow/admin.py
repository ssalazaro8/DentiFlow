from django.contrib import admin

from .models import Workflow, WorkflowUpdate

admin.site.register(Workflow)
admin.site.register(WorkflowUpdate)
