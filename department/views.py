from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from department.models import Department, DepartmentTypes
from department.serializers import DepartmentSerializer, DepartmentTypesSerializer
from user.views import PartialPutMixin


@extend_schema(tags=['DepartmentTypes'])
class DepartmentTypesViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = DepartmentTypes.objects.all()
    serializer_class = DepartmentTypesSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Department'])
class DepartmentViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
