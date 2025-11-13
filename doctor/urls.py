from django.urls import path, include
from rest_framework.routers import DefaultRouter
from doctor.views import DoctorAPIView, ConsultationsViewSet

router = DefaultRouter()
router.register('consultations', ConsultationsViewSet)

urlpatterns = [
    path('doctor/<int:department_id>/', DoctorAPIView.as_view(), name='doctor'),
    path('', include(router.urls)),
]
