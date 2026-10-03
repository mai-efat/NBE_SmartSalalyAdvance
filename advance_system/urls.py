from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView 
from django.shortcuts import redirect
from hr_core.views import NotificationListView, MarkNotificationAsReadView

from rest_framework_simplejwt.views import (
    TokenRefreshView,  # ضيفي دي هنا
)

from hr_core.views import (
    EmployeeRegisterView,
    NationalIDTokenObtainPairView,
    EmployeeProfileView,
    
)
from advances.views import UpdateAdvanceStatusView, EmployeeAdvanceHistoryAPIView


urlpatterns = [
    path('', lambda request: redirect('/advances/')),
    path('admin/', admin.site.urls),
    path('api/login/', NationalIDTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
    path('api/register/', EmployeeRegisterView.as_view(), name='employee-register'),
    path('api/profile/<str:first_name>/<str:last_name>/', EmployeeProfileView.as_view(), name='employee-profile'),
    path('api/requests/<int:advance_id>/update-status/', UpdateAdvanceStatusView.as_view(), name='hr-update-advance-status'),
    path('api/advances/', include('advances.urls')),  
    path('api/notifications/', NotificationListView.as_view(), name='notification-list'),
    path('api/notifications/<int:pk>/read/', MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    path('api/advances/history/', EmployeeAdvanceHistoryAPIView.as_view(), name='employee-advance-history')
]