from rest_framework import serializers
from .models import Salary, Wage, Payroll


class SalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Salary
        fields = '__all__'


class WageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wage
        fields = '__all__'


class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = '__all__'