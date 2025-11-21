from django.urls import path, include
from rest_framework.routers import DefaultRouter

from reception.views import PatientViewSet, PatientDoctorAPIView, PatientAnalysisAPIView

router = DefaultRouter()
router.register('patient', PatientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('doctor/patients', PatientDoctorAPIView.as_view(), name='doctor-patients'),
    path('analysis/patient/', PatientAnalysisAPIView.as_view(), name='analysis-patient'),
]
