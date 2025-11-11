from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from reception.models import Patient
from reception.serializers import PatientSerializer
from user.views import PartialPutMixin


@extend_schema(tags=['Patient'])
class PatientViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']
