from rest_framework import viewsets, generics, permissions
from hr_core.models import Department, Employee, BankAccount
from hr_core.serializers import DepartmentSerializer, EmployeeSerializer, BankAccountSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import NationalIDTokenObtainPairSerializer, NotificationSerializer
from .serializers import EmployeeFullProfileSerializer
from django.shortcuts import get_object_or_404  
from advances.permissions import IsEmployee, IsHR, IsManager 
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer

class EmployeeRegisterView(generics.CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.AllowAny]
    
    
    







class NationalIDTokenObtainPairView(TokenObtainPairView):
    serializer_class = NationalIDTokenObtainPairSerializer
    
    
    
class EmployeeProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsEmployee | IsManager]

    # دالة مساعدة لجلب الموظف بالاسم
    def get_employee(self, first_name, last_name):
        return get_object_or_404(
            Employee,
            user__first_name__iexact=first_name,
            user__last_name__iexact=last_name,
        )

    # دالة الجلب (GET)
    def get(self, request, first_name, last_name):
        employee = self.get_employee(first_name, last_name)
        serializer = EmployeeFullProfileSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # دالة التعديل الكلي (PUT)
    def put(self, request, first_name, last_name):
        employee = self.get_employee(first_name, last_name)
        serializer = EmployeeFullProfileSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # دالة التعديل الجزئي (PATCH)
    def patch(self, request, first_name, last_name):
        employee = self.get_employee(first_name, last_name)
        serializer = EmployeeFullProfileSerializer(
            employee, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class NotificationListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # جلب إشعارات الموظف الحالي فقط
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        
        # عدد الإشعارات غير المقروءة
        unread_count = notifications.filter(is_read=False).count()

        return Response({
            'unread_count': unread_count,
            'notifications': serializer.data
        }, status=status.HTTP_200_OK)
class MarkNotificationAsReadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'detail': 'تم تحديث الإشعار إلى قيد القراءة.'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'detail': 'الإشعار غير موجود.'}, status=status.HTTP_404_NOT_FOUND)