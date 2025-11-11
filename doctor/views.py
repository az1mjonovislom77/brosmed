from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from user.models import User
from user.serializers import UserCreateSerializer


@extend_schema(tags=['Doctor'])
class DoctorAPIView(ListAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(role=User.UserRoles.DOCTOR)
