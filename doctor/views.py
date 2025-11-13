from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from doctor.models import Consultations
from doctor.serializers import ConsultationsSerializer
from user.models import User
from user.serializers import UserCreateSerializer
from user.views import PartialPutMixin


@extend_schema(tags=['Doctor'])
class DoctorAPIView(ListAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        department_id = self.kwargs.get('department_id')
        return User.objects.filter(role=User.UserRoles.DOCTOR, department_id=department_id)


@extend_schema(tags=['Consultations'])
class ConsultationsViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Consultations.objects.all()
    serializer_class = ConsultationsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']
