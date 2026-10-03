from django.contrib import admin

from .models import Department, Employee, BankAccount  # مثال لتطبيق hr_core

admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(BankAccount)
