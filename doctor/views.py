from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from doctor.models import Consultations
from doctor.serializers import ConsultationsSerializer
from reception.models import Patient
from user.models import User
from user.serializers import UserCreateSerializer
from user.views import PartialPutMixin
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.response import Response


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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()
        jami_bemorlar = Patient.objects.filter(user=request.user).count()
        bugungi_bemorlar = Patient.objects.filter(created_at__date=today, user=request.user).count()
        kutayotgan = Patient.objects.filter(created_at__date=today, patient_status=Patient.PatientStatus.in_register,
                                            user=request.user).count()
        davolanayotgan = Patient.objects.filter(created_at__date=today, patient_status=Patient.PatientStatus.treating,
                                                user=request.user).count()
        sogaygan = Patient.objects.filter(user=request.user, patient_status=Patient.PatientStatus.recovered).count()

        oxirgi_konsultatsiyalar = Consultations.objects.filter(user=request.user).order_by('-created_at')[:10]

        data = {
            "jami_bemorlar": jami_bemorlar,
            "bugungi_bemorlar": bugungi_bemorlar,
            "kutayotgan": kutayotgan,
            "davolanayotgan": davolanayotgan,
            "sogaygan": sogaygan,
            'oxirgi_konsultatsiyalar': (
                ConsultationsSerializer(oxirgi_konsultatsiyalar, many=True, context={'request': request}).data if
                oxirgi_konsultatsiyalar else None)
        }

        return Response(data, status=status.HTTP_200_OK)
