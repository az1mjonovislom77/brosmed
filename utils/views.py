from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from doctor.models import Consultations
from laboratory.models import Analysis
from reception.models import Patient
from user.views import PartialPutMixin
from utils.models import ClinicAbout
from utils.serializers import ClinicAboutSerializer, ClinicStatsSerializer, ClinicStatsInputSerializer
from django.db.models import Sum, F, FloatField


@extend_schema(tags=['ClinicAbout'])
class ClinicAboutViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = ClinicAbout.objects.all()
    serializer_class = ClinicAboutSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]


@extend_schema(request=ClinicStatsInputSerializer, responses=ClinicStatsSerializer, tags=['Report'])
class ClinicStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClinicStatsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data.get('start_date') or timezone.now().date()
        end_date = serializer.validated_data.get('end_date') or timezone.now().date()

        total_income = Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed,
                                              updated_at__date__range=(start_date, end_date)).aggregate(
            total=Sum(F('paid_amount'), output_field=FloatField()))['total'] or 0.0

        data = {
            "start_date": start_date,
            "end_date": end_date,
            "jami_bemorlar": Patient.objects.filter(created_at__date__range=(start_date, end_date)).count(),
            "konsultatsiyalar": Consultations.objects.filter(created_at__date__range=(start_date, end_date)).count(),
            "tahlillar": Analysis.objects.filter(created_at__date__range=(start_date, end_date)).count(),
            "tolovlar": total_income,
        }

        output_serializer = ClinicStatsSerializer(instance=data)
        return Response(output_serializer.data, status=200)
