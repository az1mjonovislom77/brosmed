from django.urls import path, include
from rest_framework.routers import DefaultRouter

from department.views import DepartmentViewSet, DepartmentTypesViewSet, ResultViewSet

router = DefaultRouter()
router.register('department', DepartmentViewSet)
router.register('department_types', DepartmentTypesViewSet)
router.register('result', ResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
