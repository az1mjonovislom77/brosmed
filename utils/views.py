from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from department.models import Department
from doctor.models import Consultations
from reception.models import Patient, Analysis
from user.views import PartialPutMixin
from utils.models import ClinicAbout
from utils.serializers import ClinicAboutSerializer, ClinicStatsInputSerializer, ClinicStatsResponseSerializer
from django.db.models import Sum
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse
from datetime import date, timedelta


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
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        umumiy_tolov = Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed,
                                              updated_at__date__range=(start_date, end_date)).aggregate(
            total=Sum('paid_amount'))['total'] or 0.0

        umumiy_data = {
            "start_date": start_date,
            "end_date": end_date,
            "jami_bemorlar": Patient.objects.filter(created_at__date__range=(start_date, end_date)).count(),
            "konsultatsiyalar": Consultations.objects.filter(created_at__date__range=(start_date, end_date)).count(),
            "tahlillar": Analysis.objects.filter(created_at__date__range=(start_date, end_date)).count(),
            "tolovlar": umumiy_tolov,
        }

        departments_data = []

        for dep in Department.objects.all():
            dep_patients = Patient.objects.filter(department=dep, created_at__date__range=(start_date, end_date))
            dep_tolov = \
                dep_patients.filter(payment_status=Patient.PaymentStatus.confirmed).aggregate(total=Sum('paid_amount'))[
                    'total'] or 0.0
            departments_data.append({
                "department": dep.title,
                "jami_bemorlar": dep_patients.count(),
                "konsultatsiyalar": Consultations.objects.filter(patient__department=dep,
                                                                 created_at__date__range=(start_date,
                                                                                          end_date)).count(),
                "tahlillar": Analysis.objects.filter(patient__department=dep,
                                                     created_at__date__range=(start_date, end_date)).count(),
                "tolovlar": dep_tolov
            })

        response_data = {
            "umumiy": umumiy_data,
            "departments": departments_data
        }

        output = ClinicStatsResponseSerializer(response_data)
        return Response(output.data, status=200)


class ClinicStatsExportMixin:

    def get_stats(self, request):
        serializer = ClinicStatsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
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

        return {
            "umumiy": umumiy_data,
            "departments": departments_data
        }


@extend_schema(tags=['Report'])
class ClinicLastWeekAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        results = []

        for i in range(7):
            day = start_date + timedelta(days=i)
            bemorlar = Patient.objects.filter(created_at__date=day).count()
            konsultatsiyalar = Consultations.objects.filter(created_at__date=day).count()
            tahlillar = Analysis.objects.filter(created_at__date=day).count()
            tolovlar = Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed, updated_at__date=day
                                              ).aggregate(total=Sum('paid_amount'))['total'] or 0.0

            results.append({
                "day": day,
                "patients": bemorlar,
                "consultations": konsultatsiyalar,
                "tahlillar": tahlillar,
                "tolovlar": tolovlar,

            })

        return Response(results)


@extend_schema(tags=['Report'], request=ClinicStatsInputSerializer, responses={200: None})
class ClinicStatsExcelAPIView(ClinicStatsExportMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = self.get_stats(request)
        wb = Workbook()
        ws = wb.active
        ws.title = "Clinic Stats"
        ws.append(["Umumiy Statistikalar"])
        for key, value in data["umumiy"].items():
            ws.append([key, value])
        ws.append([])
        ws.append(["Bo‘limlar Statistikasi"])
        ws.append(["Department", "Bemorlar", "Konsultatsiyalar", "Tahlillar", "To‘lovlar"])
        for dep in data["departments"]:
            ws.append([
                dep["department"], dep["jami_bemorlar"], dep["konsultatsiyalar"],
                dep["tahlillar"], dep["tolovlar"]
            ])

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)

        response = HttpResponse(
            stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="clinic_stats.xlsx"'
        return response


@extend_schema(tags=['Report'], request=ClinicStatsInputSerializer, responses={200: None})
class ClinicStatsPDFAPIView(ClinicStatsExportMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = self.get_stats(request)
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        y = 800
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Klinika statistikasi")
        y -= 30
        start_date = data["umumiy"]["start_date"]
        end_date = data["umumiy"]["end_date"]
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"Hisobot davri: {start_date} - {end_date}")
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "UMUMIY:")
        y -= 20
        pdf.setFont("Helvetica", 12)
        for key, value in data["umumiy"].items():
            if key in ['start_date', 'end_date']:
                continue
            pdf.drawString(60, y, f"{key}: {value}")
            y -= 18
        y -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "DEPARTAMENTLAR:")
        y -= 20
        pdf.setFont("Helvetica", 12)
        for dep in data["departments"]:
            pdf.drawString(
                60, y,
                f"{dep['department']} → Bemor: {dep['jami_bemorlar']}, "
                f"Konsultatsiya: {dep['konsultatsiyalar']}, "
                f"Tahlil: {dep['tahlillar']}, "
                f"To‘lov: {dep['tolovlar']}"
            )
            y -= 18

        pdf.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response["Content-Disposition"] = f'attachment; filename="clinic_stats_{start_date}_{end_date}.pdf"'
        return response
