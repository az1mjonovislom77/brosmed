import json
import os
import re
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from bot import normalize_phone
from department.models import Department
from laboratory.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    AnalysisFullDetailSerializer, AnalysisDetailInputSerializer
from laboratory.utils import create_analysis_docx
from reception.models import Analysis
from user.models import User
from user.views import PartialPutMixin
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
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
            Q(status__icontains=search_value)
            | Q(patient__name__icontains=search_value)
            | Q(patient__last_name__icontains=search_value)
            | Q(patient__middle_name__icontains=search_value)
            | Q(patient__phone_number__icontains=search_value)
            | Q(department_types__title__icontains=search_value)
        ).distinct()

        output = AnalysisSerializer(queryset, many=True, context={'request': request})
        return Response(output.data)


@csrf_exempt
def check_patient(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body)
        raw_phone = body.get("phone", "").strip()
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    phone = normalize_phone(raw_phone)
    if not phone:
        return JsonResponse({"error": "Invalid phone"}, status=400)

    patient = Patient.objects.filter(phone_number=phone).first()

    if not patient:
        for p in Patient.objects.all():
            if normalize_phone(p.phone_number) == phone:
                patient = p
                break

    if not patient:
        return JsonResponse({"error": "Patient not found"}, status=404)

    dept_types = []
    departments = Department.objects.filter(patient=patient)
    seen = set()
    for dept in departments:
        for dt in dept.department_types.all():
            if dt.id not in seen:
                dept_types.append({
                    "id": dt.id,
                    "title": dt.title
                })
                seen.add(dt.id)

    if not dept_types:
        dept_types = [{"id": 1, "title": "Umumiy tahlil"}]

    return JsonResponse({
        "found": True,
        "department_types": dept_types
    })


@csrf_exempt
def export_analysis_by_phone(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST"}, status=405)

    try:
        body = json.loads(request.body)
        raw_phone = body.get("phone", "").strip()
        department_type_id = body.get("department_type_id")
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    phone = normalize_phone(raw_phone)
    if not phone:
        return JsonResponse({"error": "Invalid phone"}, status=400)

    patient = Patient.objects.filter(phone_number=phone).first()
    if not patient:
        for p in Patient.objects.all():
            if normalize_phone(p.phone_number) == phone:
                patient = p
                break
    if not patient:
        return JsonResponse({"error": "Patient not found"}, status=404)

    analyses_qs = Analysis.objects.filter(patient=patient)
    if department_type_id and str(department_type_id).isdigit():
        analyses_qs = analyses_qs.filter(department_types_id=int(department_type_id))

    analyses_qs = analyses_qs.order_by('-created_at')
    if not analyses_qs.exists():
        return JsonResponse({"error": "No analysis found"}, status=404)

    export_dir = os.path.join(settings.MEDIA_ROOT, "temp_exports")
    os.makedirs(export_dir, exist_ok=True)

    header_image_path = os.path.join(settings.STATIC_ROOT or "", "images", "header.png")
    if not os.path.exists(header_image_path):
        header_image_path = None

    files_created = []

    for analysis in analyses_qs:
        dept_name = "Umumiy"
        if analysis.department_types and analysis.department_types.title:
            dept_name = analysis.department_types.title.strip()

        created_at = analysis.created_at
        date_str = created_at.strftime("%d.%m.%Y")
        time_str = created_at.strftime("%H-%M")

        safe_dept = re.sub(r'[<>:"/\\|?*]', '_', dept_name)[:40]
        filename = f"{safe_dept}_{date_str}_{time_str}.docx"
        filepath = os.path.join(export_dir, filename)

        results_list = []
        seen_titles = set()
        time_window = timezone.timedelta(hours=2)
        start_time = created_at - time_window
        end_time = created_at + time_window

        candidate_results = AnalysisResult.objects.filter(
            patient=patient,
            created_at__gte=start_time,
            created_at__lte=end_time
        ).select_related('result').order_by('created_at')

        for ar in candidate_results:
            if not ar.result or not ar.result.title:
                continue
            title = ar.result.title.strip()
            if title in seen_titles:
                continue
            seen_titles.add(title)

            results_list.append({
                'title': title,
                'value': ar.analysis_result or '-',
                'norma': ar.result.norma or '-'
            })

        if not results_list:
            results_list = [{'title': 'Natija hali kiritilmagan', 'value': '', 'norma': ''}]

        doctor_name = "Laborant"

        if analysis.department_types:
            departments = Department.objects.filter(department_types=analysis.department_types)
            if departments.exists():
                dept = departments.first()
                staff = User.objects.filter(
                    department=dept,
                    role__in=['l', 'd'],
                    is_active=True,
                    full_name__isnull=False,
                    full_name__gt=''
                ).first()
                if staff:
                    doctor_name = staff.full_name.strip()
                else:
                    doctor_name = f"{dept.title}" if dept.title else "Laborant"

        create_analysis_docx(
            patient=patient,
            analysis=analysis,
            results_list=results_list,
            output_path=filepath,
            header_image_path=header_image_path,
            analysis_title=f"{dept_name} natijasi",
            doctor_name=doctor_name
        )

        file_url = request.build_absolute_uri(f"{settings.MEDIA_URL}temp_exports/{filename}")
        files_created.append({
            "filename": filename,
            "url": file_url
        })

    return JsonResponse({"files": files_created})


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
