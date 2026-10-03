import re
from django.utils.timesince import timesince
from rest_framework import serializers
from hr_core.models import Department, Employee, BankAccount, Notification
from advances.models import AdvanceRequest
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from hr_core.models import Employee
from django.contrib.auth.models import User
from advances.serializers import AdvanceRequestSerializer

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department_id', 'department_name']


class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Employee
        fields = [
            'national_id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'password',          # <--- الباسورد في الآخر
            'password_confirm',  # <--- تأكيد الباسورد في الآخر
        ]
        
        read_only_fields = [
            'user', 
            'employee_number', 
            'department',      
            'hire_date',
            'hourly_rate', 
            'status', 
            'probation_start', 
            'probation_end'
        ]
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "كلمتا المرور غير متطابقتين."})
        return attrs    
    
    def validate_national_id(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("الرقم القومي يجب أن يحتوي على أرقام فقط.")
        if len(value) != 14:
            raise serializers.ValidationError("الرقم القومي يجب أن يتكون من 14 رقم بالظبط.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("الرقم القومي مسجل بالفعل بحساب آخر.")
        return value
    def validate_phone(self, value):
        # النمط الخاص بأرقام الموبايل المصرية (010, 011, 012, 015)
        phone_pattern = r'^01[0125]\d{8}$'
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError("يرجى إدخال رقم هاتف مصري صحيح مكون من 11 رقم (يبدأ بـ 010 أو 011 أو 012 أو 015).")
        return value
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل.")
        return value
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "كلمتا المرور غير متطابقتين."})
        return attrs
    
    
    def create(self, validated_data):
        # 1. فصل كلمة المرور عن باقي بيانات الموظف
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
      
        national_id = validated_data.get('national_id')
        validated_data.setdefault('hourly_rate', 0.0)
        

        # 2. إنشاء حساب User جديد في جدول دجانجو تلقائياً
        # (نستخدم الـ national_id أو الـ email كاسم مستخدم username)
        user = User.objects.create(
            username=national_id,
            email=validated_data.get('email', ''),
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # 3. تشفير كلمة المرور وحفظها في الـ User
        if password:
            user.set_password(password)
            user.save()

        employee = Employee.objects.create(user=user, **validated_data)

        return employee    
        


class BankAccountSerializer(serializers.ModelSerializer):
    # ربط الحساب بالموظف تلقائياً أو عرضه بصيغة واضحة
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)

    class Meta:
        model = BankAccount
        fields = ['account_id', 'employee', 'employee_name', 'account_number', 'balance', 'status']
        






class NationalIDTokenObtainPairSerializer(TokenObtainPairSerializer):
  username_field = "national_id"

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields["national_id"] = serializers.CharField(required=True)
    self.fields.pop("username", None)

  def validate(self, attrs):
    national_id = attrs.get("national_id")
    password = attrs.get("password")

    if national_id and password:
      try:
        employee = Employee.objects.get(national_id=national_id)
        # Access the related Django User object
        user = employee.user
      except Employee.DoesNotExist:
        raise serializers.ValidationError(
            "Invalid National ID or password."
        )

      # Check the password against the actual Django User object
      if not user.check_password(password):
        raise serializers.ValidationError(
            "Invalid National ID or password."
        )

      if not user.is_active:
        raise serializers.ValidationError("This user account is inactive.")

      # Generate SimpleJWT tokens for the user
      refresh = self.get_token(user)

      return {
          "refresh": str(refresh),
          "access": str(refresh.access_token),
      }
    else:
      raise serializers.ValidationError(
          "Must include 'national_id' and 'password'."
      )
      
      
class EmployeeFullProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', read_only=True)
    advance_requests = AdvanceRequestSerializer(source='advancerequest_set', many=True, read_only=True)
    bank_account_number = serializers.CharField(source='bankaccount.account_number', read_only=True)
    department = DepartmentSerializer(read_only=True)
    class Meta:
        model = Employee
        fields = [
            'national_id', 
            'first_name', 
            'last_name', 
            'email', 
            'phone',
            'department',
            'advance_requests', # يظهر هنا كل طلباته وحالتها
            'bank_account_number', # يظهر هنا رقم الحساب فقط
        ]
    def get_bank_account(self, obj):
        try:
            # بنجيب الحساب البنكي المرتبط بالموظف مباشرة
            account = BankAccount.objects.get(employee=obj)
            return {
                "account_number": account.account_number,
                "balance": account.balance,
                "status": account.status
            }
        except BankAccount.DoesNotExist:
            return None

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
    
class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at', 'time_ago']

    def get_time_ago(self, obj):
        # إرجاع الوقت المنقضي بشكل مبسط
        
        return f"منذ {timesince(obj.created_at)}"