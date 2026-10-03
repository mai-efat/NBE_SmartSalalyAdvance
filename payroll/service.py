from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum
from hr_core.models import Employee, BankAccount

from advances.models import AdvanceRequest
from .models import Payroll, Salary, Wage

MONTHLY_WORKING_HOURS = Decimal("160")


@transaction.atomic
def calculate_payroll(employee, month, year):
  # 1. تحديد تاريخ بداية ونهاية الشهر المراد حساب البيرول له
  target_date = date(year, month, 1)
  p_start = target_date
  p_end = date(year, month, monthrange(year, month)[1])

  # 2. حساب تاريخ الصرف أوتوماتيك (أول يوم في الشهر التالي)
  pay_date = target_date + relativedelta(months=1)
  bank_account = BankAccount.objects.filter(employee=employee).first()

  # 3. جلب المرتب الساري لهذا الشهر أوتوماتيك
  salary = (
      Salary.objects.filter(
          employee=employee, effective_from__lte=target_date
      )
      .filter(Q(effective_to__gte=target_date) | Q(effective_to__isnull=True))
      .order_by("-effective_from")
      .first()
  )
  if not salary:
    raise ValueError("Employee does not have an active salary for this month.")

  # 4. حساب إجمالي ساعات العمل للشهر والسنة المحددين فقط من جدول Wages
  total_hours = (
      Wage.objects.filter(
          employee=employee, wage_date__year=year, wage_date__month=month
      ).aggregate(total=Sum("hours_worked"))["total"]
      or Decimal("0")
  )

  # شرط أساسي: لو مفيش ساعات عمل مسجلة، ممنوع يحسب بيرول وهمي!
  if total_hours == Decimal("0"):
    raise ValueError(
        f"Cannot calculate payroll: No working hours found for {employee} in"
        f" {month}/{year}."
    )

  bank_account = BankAccount.objects.filter(employee=employee).first()

  # 5. حساب معدل الساعة (المرتب الأساسي ÷ 160 ساعة)
  hourly_rate = salary.basic_salary / MONTHLY_WORKING_HOURS

  # 6. حساب الأجور الفعلية = سعر الساعة × عدد ساعات العمل الفعلية
  total_wages = hourly_rate * total_hours

  # 7. إضافة البدلات
  gross_salary = total_wages + salary.allowances

  # 8. جلب السلفة المعتمدة الخاصة بهذا الشهر فقط وغير المربوطة ببيرول سابق
  advance = (
      AdvanceRequest.objects.filter(
          employee=employee,
          status="APPROVED",
          payroll__isnull=True,
          requested_at__year=year,
          requested_at__month=month,
      )
      .select_related("policy")
      .first()
  )

  advance_deduction = Decimal("0")
  admin_fees = Decimal("0")

  if advance:
    advance_deduction = advance.approved_amount or Decimal("0")

    admin_fees = (
        advance.policy.fee if advance.policy and advance.policy.fee else Decimal("0")
    )

  # 9. إجمالي الخصومات
  total_deductions = advance_deduction + admin_fees

  # 10. صافي المرتب النهائي
  net_pay = gross_salary - total_deductions

  # 11. إنشاء سجل البيرول بالساعات والحسابات الصحيحة
  payroll, created = Payroll.objects.update_or_create(
      employee=employee,
      payroll_month=target_date,
      defaults={
          "total_base_salary": salary.basic_salary,
          "total_hours": total_hours,
          "total_wages": total_wages,
          "allowances": salary.allowances,
          "advance_deduction": advance_deduction,
          "admin_fees": admin_fees,
          "gross_salary": gross_salary,
          "total_deductions": total_deductions,
          "net_pay": net_pay,
          "pay_date": pay_date,
          "status": "CALCULATED",
          "bank_account": bank_account,
      },
  )

  # 12. ربط السلفة بالبيرول عشان ما تتخصمش تاني
  if advance:
    advance.payroll = payroll
    advance.save(update_fields=["payroll"])

  # 13. تحديث وإضافة صافي المرتب لرصيد الحساب البنكي للموظف
  if bank_account:
    bank_account.balance = (bank_account.balance or Decimal("0")) + net_pay
    bank_account.save(update_fields=["balance"])

  return payroll