from django.contrib import admin
from .models import Salary, Wage, Payroll  # استخدم النماذج الموجودة فعلياً

# تسجيل النماذج في لوحة التحكم
admin.site.register(Salary)
admin.site.register(Wage)
admin.site.register(Payroll)