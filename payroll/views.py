from rest_framework import viewsets

from .models import Salary, Wage, Payroll
from .serializers import (
    SalarySerializer,
    WageSerializer,
    PayrollSerializer
)


class SalaryViewSet(viewsets.ModelViewSet):
    queryset = Salary.objects.all()
    serializer_class = SalarySerializer


class WageViewSet(viewsets.ModelViewSet):
    queryset = Wage.objects.all()
    serializer_class = WageSerializer


class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer