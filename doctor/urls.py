from django.urls import path

from doctor.views import DoctorAPIView

urlpatterns = [
    path('doctor/', DoctorAPIView.as_view(), name='doctor'),
]
