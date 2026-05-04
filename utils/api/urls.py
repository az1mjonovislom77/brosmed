from django.urls import path, include
from rest_framework.routers import DefaultRouter
from utils.api.views import ClinicStatsAPIView, ClinicAboutViewSet, ClinicStatsExcelAPIView, ClinicStatsPDFAPIView, \
    ClinicLastWeekAPIView

router = DefaultRouter()
router.register('clinicabout', ClinicAboutViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('report/', ClinicStatsAPIView.as_view()),
    path('clinic/stats/excel/', ClinicStatsExcelAPIView.as_view(), name='clinic-stats-excel'),
    path('clinic/stats/pdf/', ClinicStatsPDFAPIView.as_view(), name='clinic-stats-pdf'),
    path('clinic/last_week/', ClinicLastWeekAPIView.as_view(), name='clinic-stats-week'),
]