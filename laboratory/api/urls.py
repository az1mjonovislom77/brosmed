from django.urls import path, include
from rest_framework.routers import DefaultRouter
from laboratory.api.views import AnalysisViewSet, AnalysisDetailByPatient

router = DefaultRouter()
router.register('analysis', AnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(router.urls)),
    path('patient/result', AnalysisDetailByPatient.as_view(), name='analysis-result'),

]