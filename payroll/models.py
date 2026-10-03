from django.db import models
from hr_core.models import Employee


class Salary(models.Model):
    salary_id = models.BigAutoField(primary_key=True)

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        db_column="employee_id"
    )

    basic_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    allowances = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True
    )
   

    status = models.CharField(
        max_length=50,
        default="ACTIVE"
    )

    class Meta:
        db_table = "salary"

    def __str__(self):
        return f"{self.employee} - {self.basic_salary}"


class Wage(models.Model):
    wage_id = models.BigAutoField(primary_key=True)

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        db_column="employee_id"
    )

    wage_date = models.DateField()

    hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    class Meta:
        db_table = "wages"

    def __str__(self):
        return f"{self.employee} - {self.wage_date} - {self.hours_worked} hours"


class Payroll(models.Model):
    payroll_id = models.BigAutoField(primary_key=True)

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        db_column="employee_id"
    )

    payroll_month = models.DateField()

    total_base_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    total_hours = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0.00
    )

    total_wages = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    

    allowances = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    advance_deduction = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    admin_fees = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    gross_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    total_deductions = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

    net_pay = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )

   
    pay_date = models.DateField()

    status = models.CharField(
        max_length=50,
        default="CALCULATED"
    )
    bank_account = models.ForeignKey(
      "hr_core.BankAccount",
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name="payrolls",
  )

    class Meta:
        db_table = "payrolls"

        constraints = [
            models.UniqueConstraint(
                fields=["employee", "payroll_month"],
                name="unique_employee_payroll_month"
            )
        ]

    def __str__(self):
        return f"{self.employee} - {self.payroll_month}"