from django.urls import include, path
from .views import AdvanceRequestCreateAPIView

urlpatterns = [
    path('request/', AdvanceRequestCreateAPIView.as_view(), name='api_advance_request'),

]