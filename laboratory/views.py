import json
import os
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from laboratory.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    AnalysisFullDetailSerializer, AnalysisDetailInputSerializer
from reception.models import Analysis
from user.models import User
from user.views import PartialPutMixin
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings
from .utils import create_analysis_docx
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from reception.models import Patient, AnalysisResult


@extend_schema(tags=['Analysis'])
class AnalysisViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnalysisPostSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()

        dailyanalysiscount = Analysis.objects.filter(created_at__date=today).count()
        totalanalysiscount = Analysis.objects.all().count()
        newanalysiscount = Analysis.objects.filter(status=Analysis.Status.new, created_at__date=today).count()
        inprogressalaysiscount = Analysis.objects.filter(status=Analysis.Status.in_progress,
                                                         created_at__date=today).count()
        lastanalysis = Analysis.objects.all().order_by('-created_at')[:10]
        finishedanalysiscount = Analysis.objects.filter(status=Analysis.Status.finished, created_at__date=today).count()

        data = {
            'kunlik_tahlil': dailyanalysiscount,
            'jami_tahlil': totalanalysiscount,
            'yangi_tahlil': newanalysiscount,
            'jarayondagi_tahlil': inprogressalaysiscount,
            'yakunlangan_tahlil': finishedanalysiscount,
            'oxirgi_tahlillar': (AnalysisSerializer(lastanalysis, many=True, context={'request': request}).data if
                                 lastanalysis else None)
        }

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(methods=['POST'], request=AnalysisSearchInputSerializer,
                   responses={200: AnalysisSerializer(many=True)}, )
    @action(detail=False, methods=['post'])
    def search(self, request):
        serializer = AnalysisSearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        search_value = serializer.validated_data['search']

        queryset = Analysis.objects.filter(
            Q(analysis_result__icontains=search_value)
            | Q(analysis_result_uz__icontains=search_value)
            | Q(analysis_result_ru__icontains=search_value)
            | Q(status__icontains=search_value)
            | Q(patient__name__icontains=search_value)
            | Q(patient__last_name__icontains=search_value)
            | Q(patient__middle_name__icontains=search_value)
            | Q(patient__phone_number__icontains=search_value)
            | Q(department_types__title__icontains=search_value)
        ).distinct()

        output = AnalysisSerializer(queryset, many=True, context={'request': request})
        return Response(output.data)


@csrf_exempt
def export_analysis_by_phone(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    phone = body.get('phone')
    if not phone:
        return JsonResponse({"error": "phone required"}, status=400)

    patient = Patient.objects.filter(phone_number=phone).first()
    if not patient:
        return JsonResponse({"error": "Patient not found"}, status=404)

    results_qs = AnalysisResult.objects.filter(patient=patient) \
        .select_related('result') \
        .order_by('-created_at')

    results_list = []
    seen_titles = set()

    for ar in results_qs:
        if ar.result:
            title = str(ar.result).strip()
            norma = getattr(ar.result, 'norma', '') or ''
        else:
            title = f"[Noma'lum {ar.id}]"
            norma = ''

        value = ar.analysis_result or ''

        if title and title not in seen_titles:
            results_list.append({
                'title': title,
                'value': value,
                'norma': norma
            })
            seen_titles.add(title)

    if not results_list:
        results_list = [
            {'title': '', 'value': '', 'norma': ''},
            {'title': '', 'value': '', 'norma': ''},
        ]

    analysis_title = "Анализ"
    if patient.department_types and patient.department_types.title:
        analysis_title = patient.department_types.title.strip()

    doctor_name = "Laborant"

    if patient.department_types and patient.department_types.department:
        dept = patient.department_types.department

        staff = User.objects.filter(department=dept, role__in=['l', 'd'], is_active=True, full_name__isnull=False,
                                    full_name__gt='').first()

        if staff:
            doctor_name = staff.full_name.strip()
        else:
            doctor_name = f"{dept.title}" if dept.title else "Laborant"
    elif patient.department_types:
        doctor_name = f"{patient.department_types.title}"
    print(f"[DOCX] Sarlavha: {analysis_title} | Doktor: {doctor_name}")

    class DummyAnalysis:
        id = 0
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


@extend_schema(tags=['Analysis'])
class AnalysisDetailByPatient(APIView):

    serializer_class = AnalysisDetailInputSerializer

    def post(self, request):
        serializer = AnalysisDetailInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        patient_id = serializer.validated_data['patient_id']
        analysis_id = serializer.validated_data['analysis_id']

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient topilmadi"}, status=404)

        try:
            analysis = Analysis.objects.get(id=analysis_id, patient=patient)
        except Analysis.DoesNotExist:
            return Response({"error": "Analysis topilmadi yoki bu patientga tegishli emas"}, status=404)

        output = AnalysisFullDetailSerializer(analysis, context={"request": request})
        return Response(output.data, status=200)
