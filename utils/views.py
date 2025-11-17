from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from department.models import Department
from doctor.models import Consultations
from laboratory.models import Analysis
from reception.models import Patient
from user.views import PartialPutMixin
from utils.models import ClinicAbout
from utils.serializers import ClinicAboutSerializer, ClinicStatsSerializer, ClinicStatsInputSerializer, \
    ClinicStatsResponseSerializer
from django.db.models import Sum


@extend_schema(tags=['ClinicAbout'])
class ClinicAboutViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = ClinicAbout.objects.all()
    serializer_class = ClinicAboutSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Report'], request=ClinicStatsInputSerializer, responses=ClinicStatsResponseSerializer)
class ClinicStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClinicStatsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data.get('start_date') or timezone.now().date()
        end_date = serializer.validated_data.get('end_date') or timezone.now().date()

        umumiy_tolov = Patient.objects.filter(
            payment_status=Patient.PaymentStatus.confirmed,
            updated_at__date__range=(start_date, end_date)
        ).aggregate(total=Sum('paid_amount'))['total'] or 0.0

        umumiy_data = {
            "start_date": start_date,
            "end_date": end_date,
            "jami_bemorlar": Patient.objects.filter(
                created_at__date__range=(start_date, end_date)
            ).count(),
            "konsultatsiyalar": Consultations.objects.filter(
                created_at__date__range=(start_date, end_date)
            ).count(),
            "tahlillar": Analysis.objects.filter(
                created_at__date__range=(start_date, end_date)
            ).count(),
            "tolovlar": umumiy_tolov,
        }

        departments_data = []

        for dep in Department.objects.all():
            dep_patients = Patient.objects.filter(
                department=dep,
                created_at__date__range=(start_date, end_date)
            )

            dep_tolov = dep_patients.filter(
                payment_status=Patient.PaymentStatus.confirmed
            ).aggregate(total=Sum('paid_amount'))['total'] or 0.0

            departments_data.append({
                "department": dep.title,
                "jami_bemorlar": dep_patients.count(),
                "konsultatsiyalar": Consultations.objects.filter(
                    patient__department=dep,
                    created_at__date__range=(start_date, end_date)
                ).count(),
                "tahlillar": Analysis.objects.filter(
                    patient__department=dep,
                    created_at__date__range=(start_date, end_date)
                ).count(),
                "tolovlar": dep_tolov
            })

        response_data = {
            "umumiy": umumiy_data,
            "departments": departments_data
        }

        output = ClinicStatsResponseSerializer(response_data)
        return Response(output.data, status=200)
