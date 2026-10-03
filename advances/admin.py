from django.contrib import admin
from .models import AdvancePolicy, AdvanceRequest
from hr_core.models import Notification

admin.site.register(AdvancePolicy)
admin.site.register(AdvanceRequest)
admin.site.register(Notification)