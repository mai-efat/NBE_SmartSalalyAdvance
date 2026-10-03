from datetime import date, timezone
from dateutil.relativedelta import relativedelta  # مكتبة ممتازة لحساب الشهور والسنين بدقة
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model


class Department(models.Model):
    department_id = models.BigAutoField(primary_key=True)
    department_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.department_name


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # ربط جدول الموظف بجدول الـ User
    employee_id = models.BigAutoField(primary_key=True)
    national_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    hire_date = models.DateField(default=date.today, blank=True)
    probation_start = models.DateField(blank=True, null=True)
    probation_end = models.DateField(blank=True, null=True)
    
    def validate_password(self, value):
     validate_password(value)
     return value
    
    def save(self, *args, **kwargs):
       
        if self.hire_date:
            if not self.probation_start:
                self.probation_start = self.hire_date
            
            if not self.probation_end:
                self.probation_end = self.hire_date + relativedelta(months=3)
                
        super().save(*args, **kwargs)
    
   
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        db_column='department_id'
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('resigned', 'Resigned'),
        ('terminated', 'Terminated'),
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.0)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES, default='Inactive')

    class Meta:
        db_table = 'employees'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class BankAccount(models.Model):
    
    
    account_id = models.BigAutoField(primary_key=True)
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        db_column='employee_id'
    )
    account_number = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    status = models.CharField(max_length=20,choices=STATUS_CHOICES, default='Inactive')

    class Meta:
        db_table = 'bank_accounts'

    def __str__(self):
        return f"Account {self.account_number} - {self.employee}"
    
    
    

User = get_user_model()
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('ADVANCE_APPROVED', 'موافقة على سلفة'),
        ('ADVANCE_REJECTED', 'رفض طلب سلفة'),
        ('SALARY_DEPOSIT', 'إيداع راتب'),
        ('DEDUCTION_REMINDER', 'تذكير بموعد القسط'),
        ('GENERAL', 'عام'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='GENERAL')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
from .models import Notification

def create_notification(user, title, message, notification_type='GENERAL'):
    """دالة مساعدة لإنشاء إشعار للمستخدم"""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )