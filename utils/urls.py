from django.urls import path, include
from rest_framework.routers import DefaultRouter

from utils.serializers import ClinicStatsInputSerializer
from utils.views import ClinicAboutViewSet, ClinicStatsAPIView

router = DefaultRouter()
router.register('clinicabout', ClinicAboutViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('report/', ClinicStatsAPIView.as_view()),
]
