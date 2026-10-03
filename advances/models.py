from datetime import date

from django.db import models
from hr_core.models import Employee
from payroll.models import Payroll


class AdvancePolicy(models.Model):
    policy_id = models.BigAutoField(primary_key=True)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2)
    requests_per_month = models.IntegerField(default=1)
    probation_allowed = models.BooleanField(default=False)
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    

    class Meta:
        db_table = 'advance_policies'

    def __str__(self):
        return f"Policy {self.policy_id}"


class AdvanceRequest(models.Model):
    
    advance_id = models.BigAutoField(primary_key=True)
    request_date = models.DateField(default=date.today, editable=False)
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        db_column='employee_id'
    )
    policy = models.ForeignKey(
        AdvancePolicy, 
        on_delete=models.PROTECT, 
        db_column='policy_id'
    )
    payroll = models.ForeignKey(
        Payroll, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='payroll_id'
    )
    reason = models.TextField(blank=True, null=True)
     
    STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('CANCELLED', 'Cancelled'),
]
    requested_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='PENDING')
    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
   

    class Meta:
        
        db_table = 'advance_requests'
    def save(self, *args, **kwargs):
        # لو الحالة APPROVED والمبلغ المعتمد مش متسجل، خليه يساوي المبلغ المطلوب أوتوماتيك
        if self.status == 'APPROVED' and not self.approved_amount:
            self.approved_amount = self.requested_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Advance Request #{self.advance_id} - {self.requested_amount}"