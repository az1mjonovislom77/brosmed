import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.http import FileResponse
from django.conf import settings
from pdf_service.generator.pdf_utils import convert_docx_to_pdf, create_analysis_docx
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

        next_analysis = Analysis.objects.filter(
            patient=patient,
            department_types=analysis.department_types,
            created_at__gt=analysis.created_at
        ).order_by("created_at").first()

        results_qs = AnalysisResult.objects.filter(
            patient=patient,
            result__department_types=analysis.department_types,
            created_at__gte=analysis.created_at
        ).select_related('result').order_by('-created_at')

        if next_analysis:
            results_qs = results_qs.filter(created_at__lt=next_analysis.created_at)

        results_list = []
        for ar in results_qs:
            title = ar.result.title if ar.result else f"[Noma'lum {ar.id}]"
            norma = ar.result.norma if ar.result else ''
            value = ar.analysis_result or ''
            results_list.append({'title': title, 'value': value, 'norma': norma})

        if not results_list:
            results_list = [{'title': '', 'value': '', 'norma': ''}]

        analysis_title = (
            analysis.department_types.title.strip()
            if analysis.department_types and analysis.department_types.title
            else "Analiz"
        )

        base_name = patient.name or "analysis"
        docx_name = f"{base_name}.docx"
        pdf_name = f"{base_name}.pdf"

        export_dir = getattr(settings, 'MEDIA_ROOT', '/tmp')
        docx_path = os.path.join(export_dir, docx_name)

        header_image_path = os.path.join(settings.MEDIA_ROOT, "images", "logo.jpg")

        create_analysis_docx(
            patient=patient,
            analysis=analysis,
            results_list=results_list,
            output_path=docx_path,
            header_image_path=header_image_path,
            analysis_title=analysis_title
        )

        pdf_path = convert_docx_to_pdf(docx_path)

        if os.path.exists(docx_path):
            os.remove(docx_path)

        return FileResponse(
            open(pdf_path, 'rb'),
            as_attachment=True,
            filename=pdf_name,
            content_type='application/pdf'
        )
