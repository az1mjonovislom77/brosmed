from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reception.utils import ExportAnalysisByPatientView
from reception.views import PatientViewSet, PatientDoctorAPIView, PatientAnalysisAPIView, \
    DiseaseViewSet, PatientSearchAPIView, PatientDiseasesAPIView

router = DefaultRouter()
router.register('patient', PatientViewSet)
router.register('disease', DiseaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('doctor/patients', PatientDoctorAPIView.as_view(), name='doctor-patients'),
    path('analysis/patient/', PatientAnalysisAPIView.as_view(), name='analysis-patient'),
    path('export-analysis/', ExportAnalysisByPatientView.as_view(), name='export_analysis_by_patient'),
    path('search/patient/', PatientSearchAPIView.as_view(), name='search_patient'),
    path('patient/<int:patient_id>/diseases/', PatientDiseasesAPIView.as_view(), name='patient-diseases'),
]
