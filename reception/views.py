from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.response import Response
from reception.models import Patient
from reception.serializers import PatientSerializer
from user.views import PartialPutMixin
from datetime import timedelta


@extend_schema(tags=['Patient'])
class PatientViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()
        one_year_ago = today - timedelta(days=365)

        qabul_qilinganlar = Patient.objects.filter().count()
        bugungi_bemorlar = Patient.objects.filter(created_at__date=today).count()
        erkaklar = Patient.objects.filter(gender=Patient.GenderChoice.MALE).count()
        ayollar = Patient.objects.filter(gender=Patient.GenderChoice.FEMALE).count()
        yangi_tugilganlar = Patient.objects.filter(birth_date__gte=one_year_ago).count()
        oxirgi_bemorlar = Patient.objects.all().order_by('-created_at')[:10]

        data = {
            "qabul_qilinganlar": qabul_qilinganlar,
            "bugungi_bemorlar": bugungi_bemorlar,
            "erkaklar": erkaklar,
            "ayollar": ayollar,
            "yangi_tugilganlar": yangi_tugilganlar,
            'oxirgi_bemorlar': (PatientSerializer(oxirgi_bemorlar, many=True, context={'request': request}).data if
                                oxirgi_bemorlar else None)
        }

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=['Patient'])
class PatientDoctorAPIView(ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user).exclude(
            patient_status=Patient.PatientStatus.finished).order_by('-created_at')
