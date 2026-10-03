from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import AdvancePolicy, AdvanceRequest


def create_advance_request(employee, requested_amount):
    # 1. التحقق من أن الموظف نشط (يُفضل وضعه في البداية)
    if employee.status != 'active':
        raise ValidationError("Employee must be active to request an advance.")

    # Get the global policy
    try:
        policy = AdvancePolicy.objects.get(policy_id=1)
    except AdvancePolicy.DoesNotExist:
        raise ValidationError("Advance policy configuration not found.")

    # 2. التحقق من أن المبلغ أكبر من الصفر
    if requested_amount <= 0:
        raise ValidationError("Amount must be greater than zero.")

    # 3. التحقق من الحد الأقصى للمبلغ
    if requested_amount > policy.max_amount:
        raise ValidationError("Requested amount exceeds policy maximum.")

    # 4. التحقق من فترة الاختبار (Probation)
    today = timezone.now().date()
    in_probation = False

    if employee.hire_date:
        probation_end_date = employee.hire_date + relativedelta(months=3)
        in_probation = employee.hire_date <= today <= probation_end_date

    if in_probation and not policy.probation_allowed:
        raise ValidationError("Employee cannot request an advance during probation.")

    # 5. التحقق من السماح بطلب واحد فقط في الشهر
    request_count = AdvanceRequest.objects.filter(
        employee=employee,
        requested_at__year=today.year,
        requested_at__month=today.month
    ).count()

    if request_count >= 1:
        raise ValidationError("Employee can request only one advance per month.")

    # 6. حساب التكلفة
    advance_cost = requested_amount + policy.fee

    # 7. إنشاء الطلب في قاعدة البيانات
    advance_request = AdvanceRequest.objects.create(
        employee=employee,
        policy=policy,
        requested_amount=requested_amount,
        status="PENDING"
    )

    return advance_request, advance_cost