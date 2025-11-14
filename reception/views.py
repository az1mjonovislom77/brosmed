from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from reception.models import Patient
from reception.serializers import PatientSerializer
from user.views import PartialPutMixin


@extend_schema(tags=['Patient'])
class PatientViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()
        qabul_qilinganlar = Patient.objects.filter().count()
        bugungi_bemorlar = Patient.objects.filter(created_at__date=today).count()
        erkaklar = Patient.objects.filter(gender=Patient.GenderChoice.MALE).count()
        ayollar = Patient.objects.filter(gender=Patient.GenderChoice.FEMALE).count()
        yangi_tugilganlar = Patient.objects.filter(birth_date=today).count()


@extend_schema(tags=['Patient'])
class PatientDoctorAPIView(ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user).exclude(patient_status=Patient.PatientStatus.finished)
