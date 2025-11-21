from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.http import FileResponse
from django.utils import timezone
import os
from django.conf import settings
from laboratory.utils import create_analysis_docx
from .models import Patient, AnalysisResult, Analysis, User
from .serializers import ExportAnalysisSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['Export'])
class ExportAnalysisByPatientView(APIView):
    serializer_class = ExportAnalysisSerializer

    @swagger_auto_schema(request_body=ExportAnalysisSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        patient_id = serializer.validated_data['patient_id']
        analysis_id = serializer.validated_data['analysis_id']
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        analysis = Analysis.objects.filter(id=analysis_id, patient_id=patient_id).first()
        if not analysis:
            return Response({"error": "Analysis not found for this patient"}, status=status.HTTP_404_NOT_FOUND)
        results_qs = AnalysisResult.objects.filter(patient=patient).select_related('result').order_by('-created_at')
        results_list = []
        for ar in results_qs:
            title = ar.result.title if ar.result else f"[Noma'lum {ar.id}]"
            norma = ar.result.norma if ar.result else ''
            value = ar.analysis_result or ''
            results_list.append({'title': title, 'value': value, 'norma': norma})

        if not results_list:
            results_list = [{'title': '', 'value': '', 'norma': ''}]

        analysis_title = analysis.department_types.title.strip() if analysis.department_types and analysis.department_types.title else "Analiz"

        doctor_name = "Laborant"
        if analysis.department_types and analysis.department_types.department:
            dept = analysis.department_types.department
            staff = User.objects.filter(
                department=dept, role__in=['l', 'd'], is_active=True, full_name__isnull=False, full_name__gt=''
            ).first()
            if staff:
                doctor_name = staff.full_name.strip()
            elif analysis.department_types.title:
                doctor_name = analysis.department_types.title

        class DummyAnalysis:
            id = analysis_id
            created_at = timezone.now()

        analysis_obj = DummyAnalysis()
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        out_name = f"analysis_{patient.id}_{timestamp}.docx"
        out_path = os.path.join(getattr(settings, 'MEDIA_ROOT', '/tmp'), out_name)
        header_image_path = "/mnt/data/51cfb6cc-75b8-476e-a370-7a187b7af31b.png"

        create_analysis_docx(
            patient=patient,
            analysis=analysis_obj,
            results_list=results_list,
            output_path=out_path,
            header_image_path=header_image_path,
            analysis_title=analysis_title,
            doctor_name=doctor_name
        )

        return FileResponse(open(out_path, 'rb'), as_attachment=True, filename=out_name)
