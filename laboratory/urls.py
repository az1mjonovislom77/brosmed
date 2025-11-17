from django.urls import path, include
from rest_framework.routers import DefaultRouter

from laboratory.views import AnalysisViewSet, ResultViewSet

router = DefaultRouter()
router.register('analysis', AnalysisViewSet)
router.register('result', ResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
