from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from department.api.serializers import DepartmentSerializer, DepartmentTypesSerializer, ResultSerializer, \
    AnalysisResultPostSerializer, AnalysisResultCreateSerializer
from user.views.user_views import PartialPutMixin
from department.selectors import departments as department_selectors

@extend_schema(tags=['DepartmentTypes'])
class DepartmentTypesViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = department_selectors.get_all_department_types()
    serializer_class = DepartmentTypesSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Department'])
class DepartmentViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = department_selectors.get_all_departments()
    serializer_class = DepartmentSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Result'])
class ResultViewSet(viewsets.ModelViewSet, PartialPutMixin):
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_queryset(self):
        return department_selectors.get_all_results()


@extend_schema(tags=['AnalysisResult'])
class AnalysisResultViewSet(viewsets.ModelViewSet):
    queryset = department_selectors.get_all_analysis_results()
    serializer_class = AnalysisResultCreateSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        many = isinstance(data, list)
        serializer = self.get_serializer(data=data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(AnalysisResultPostSerializer(serializer.instance, many=many).data,
                        status=status.HTTP_201_CREATED, headers=headers)