from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from user.views import PartialPutMixin
from utils.models import ClinicAbout
from utils.serializers import ClinicAboutSerializer


@extend_schema(tags=['ClinicAbout'])
class ClinicAboutViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = ClinicAbout.objects.all()
    serializer_class = ClinicAboutSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
