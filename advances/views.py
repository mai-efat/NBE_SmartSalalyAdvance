from datetime import date

from django.db.models.aggregates import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from hr_core.models import BankAccount, Employee
from .serializers import  AdvancePolicy, AdvanceRequestHistorySerializer, AdvanceRequestSerializer, Decimal
from rest_framework import generics, permissions, status
from django.db import transaction
from .permissions import IsEmployee, IsHR, IsManager  
from .models import AdvanceRequest
from rest_framework_simplejwt.authentication import JWTAuthentication
from payroll.models import Salary, Wage
from hr_core.models import Employee
from .serializers import AdvanceRequestSerializer
from hr_core.models import create_notification
MONTHLY_WORKING_HOURS = Decimal("160")  # عدد ساعات العمل الشهري

class AdvanceRequestCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsEmployee | IsManager]

    def post(self, request):
        serializer = AdvanceRequestSerializer(data=request.data)
        if serializer.is_valid():
            # 1. جلب الموظف بشكل آمن يمنع الـ Error
            try:
                employee_instance = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                return Response(
                    {"error": "المستخدم الحالي غير مرتبط بحساب موظف."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            policy_instance = AdvancePolicy.objects.first()
            if not policy_instance:
                return Response(
                    {"error": "لا توجد سياسة سلف معرفة في النظام حالياً."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. حماية حقل تاريخ التعيين لمنع الـ AttributeError
            if not policy_instance.probation_allowed:
                if not employee_instance.hire_date:
                    return Response(
                        {"error": "لا يمكن تقديم سلفة لأن تاريخ تعيين الموظف غير مسجل."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
              
                from datetime import date
                service_months = (date.today().year - employee_instance.hire_date.year) * 12 + (date.today().month - employee_instance.hire_date.month)
                
                if service_months < 3:
                    return Response(
                        {"error": "عذراً، لا يمكنك تقديم طلب سلفة لأنك ما زلت في فترة التجربة."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                  
            requested_amount = serializer.validated_data.get('requested_amount')

            # 3. تصحيح شرط الحد الأقصى
            if requested_amount and requested_amount >= policy_instance.max_amount:
                return Response(
                    {"error": f"المبلغ المطلوب يتجاوز الحد الأقصى المسموح به وهو {policy_instance.max_amount}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. منع الطلبات المكررة
            has_pending_request = AdvanceRequest.objects.filter(
                employee=employee_instance, 
                status='PENDING'
            ).exists()

            if has_pending_request:
                return Response(
                    {"error": "لا يمكن تقديم طلب جديد؛ لديك بالفعل طلب سلفة قيد الانتظار."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # 5. حساب الأجر المكتسب لهذا الشهر بناءً على ساعات العمل
        today = date.today()
        salary = Salary.objects.filter(
            employee=employee_instance,
            effective_from__lte=today
        ).order_by("-effective_from").first()

        if not salary:
            return Response(
                {"error": "لا يوجد راتب أساسي مسجل ومفعل لهذا الموظف."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_hours = Wage.objects.filter(
            employee=employee_instance,
            wage_date__year=today.year,
            wage_date__month=today.month
        ).aggregate(total=Sum("hours_worked"))["total"] or Decimal("0")

        if total_hours == Decimal("0"):
            return Response(
                {"error": "لم يتم تسجيل أي ساعات عمل لك في هذا الشهر حتى الآن لطلب سلفة."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hourly_rate = salary.basic_salary / MONTHLY_WORKING_HOURS
        earned_salary = total_hours * hourly_rate

        requested_amount = Decimal(str(serializer.validated_data.get('requested_amount', 0)))

        # 6. التحقق من تجاوز الأجر المكتسب أو الحد الأقصى للسياسة
        if requested_amount > earned_salary:
            return Response(
                {
                    "error": (
                        f"عذراً، المبلغ المطلوب ({requested_amount} ج.م) يتجاوز أجر ساعات عملك المكتسبة "
                        f"لهذا الشهر والتي تبلغ ({earned_salary:.2f} ج.م) بناءً على {total_hours} ساعة عمل."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )  
            # 5. الحفظ
        serializer.save(
                employee=employee_instance, 
                policy=policy_instance, 
                status='PENDING'
            )

        return Response(
                {
                    "message": "Advance request created successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



def transfer_amount_to_bank(advance_request):
    print(f"Checking status: {advance_request.status}")
    
    if advance_request.status == 'APPROVED':
        employee = advance_request.employee
        # ملاحظة: تأكدي هل اسم الحقل في Model المباشر هو amount أم requested_amount
        amount = getattr(advance_request, 'requested_amount', getattr(advance_request, 'amount', 0))
        print(f"Employee: {employee}, Amount: {amount}")
        
        try:
            bank_account = BankAccount.objects.get(employee_id=employee.employee_id)
            print(f"Old Balance: {bank_account.balance}")
            
            bank_account.balance += amount
            bank_account.save()
            
            print(f"New Balance Updated Successfully to: {bank_account.balance}")
            return True
        except BankAccount.DoesNotExist:
            print("Error: Bank account not found for this employee!")
            return False
            
    return False


class UpdateAdvanceStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    queryset = AdvanceRequest.objects.all()
    serializer_class = AdvanceRequestSerializer
    lookup_field = 'advance_id'

    def get(self, request, *args, **kwargs):
        advance_request = self.get_object()
        serializer = self.get_serializer(advance_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        advance_request = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['APPROVED', 'REJECTED']:
            return Response(
                {"error": "Invalid status. Must be 'APPROVED' or 'REJECTED'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            advance_request.status = new_status
            advance_request.save()
            
            # 1. تحويل المبلغ للبنك في حالة الموافقة
            if new_status == 'APPROVED':
                transfer_amount_to_bank(advance_request)
            
            # 2. جلب قيمة المبلغ للتنبه بأسلوب أمن (أياً كان اسم الحقل عندك)
            amount_value = getattr(advance_request, 'requested_amount', getattr(advance_request, 'amount', 0))

            # 3. إنشاء الإشعار بناءً على الحالة (داخل block الـ update)
            if new_status == 'APPROVED':
                create_notification(
                    user=advance_request.employee.user,
                    title="Advance Request Approved",
                    message=f"Your advance request of {amount_value:,} EGP has been approved.",
                    notification_type="ADVANCE_APPROVED"
                )
            elif new_status == 'REJECTED':
                create_notification(
                    user=advance_request.employee.user,
                    title="Advance Request Rejected",
                    message="Sorry, your advance request has been rejected. Please contact HR for more details.",
                    notification_type="ADVANCE_REJECTED"
                )

            return Response(
                {
                    "message": f"Advance request has been {new_status.lower()} successfully.",
                    "request_id": advance_request.advance_id,
                    "status": advance_request.status
                },
                status=status.HTTP_200_OK
            )
    
    
    
    
    
    
    
    
    
    
    
    
    
def transfer_amount_to_bank(advance_request):
    # طباعة للتأكد من حالة الطلب والمبلغ
    print(f"Checking status: {advance_request.status}")
    
    if advance_request.status == 'APPROVED':
        employee = advance_request.employee
        amount = advance_request.requested_amount
        print(f"Employee: {employee}, Amount: {amount}")
        
        try:
            # استخدام employee_id لضمان جلب الحساب الصحيح بدقة
            bank_account = BankAccount.objects.get(employee_id=employee.employee_id)
            print(f"Old Balance: {bank_account.balance}")
            
            bank_account.balance += amount
            bank_account.save()
            
            print(f"New Balance Updated Successfully to: {bank_account.balance}")
            return True
        except BankAccount.DoesNotExist:
            print("Error: Bank account not found for this employee!")
            return False
            
    return False





class EmployeeAdvanceHistoryAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated | IsEmployee | IsManager]

    def get(self, request):      
            employee = Employee.objects.get(user=request.user)
            advances = (
            AdvanceRequest.objects.filter(employee=employee)
            .order_by("-request_date")
        )
      
        # 3. تحويل البيانات إلى JSON وإرجاعها
            serializer = AdvanceRequestHistorySerializer(advances, many=True)
            return Response(
            {
                "count": advances.count(),
                "results": serializer.data
            },
            status=status.HTTP_200_OK
        )