from django.urls import path

from doctor.views import DoctorAPIView

urlpatterns = [
    path('doctor/<int:department_id>/', DoctorAPIView.as_view(), name='doctor'),
]
