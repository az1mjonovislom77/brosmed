from django.urls import path, include
from rest_framework.routers import DefaultRouter

from laboratory.views import AnalysisViewSet, ResultViewSet, ResultByDepartmentDetailAPIView

router = DefaultRouter()
router.register('analysis', AnalysisViewSet)
router.register('result', ResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('department/result/<int:department_type_id>/', ResultByDepartmentDetailAPIView.as_view(),
         name='results-by-department'),

]
