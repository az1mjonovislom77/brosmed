from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from laboratory.models import Analysis
from laboratory.serializers import AnalysisSerializer
from user.views import PartialPutMixin


@extend_schema(tags=['Analysis'])
class AnalysisViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']
