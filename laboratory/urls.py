from django.urls import path, include
from rest_framework.routers import DefaultRouter

from laboratory.views import AnalysisViewSet, AnalysisDetailByPatient

router = DefaultRouter()
router.register('analysis', AnalysisViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('analysis/user', AnalysisDetailByPatient.as_view(), name='analysis-user'),

]
