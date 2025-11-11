from django.urls import path, include
from rest_framework.routers import DefaultRouter

from reception.views import PatientViewSet

router = DefaultRouter()
router.register('patient', PatientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
