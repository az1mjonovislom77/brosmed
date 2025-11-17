from django.urls import path, include
from rest_framework.routers import DefaultRouter

from utils.views import ClinicStatsAPIView, ClinicAboutViewSet

router = DefaultRouter()
router.register('clinicabout', ClinicAboutViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('report/', ClinicStatsAPIView.as_view()),
]
