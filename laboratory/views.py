import json
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from bot import normalize_phone
from department.models import Department
from laboratory.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    AnalysisFullDetailSerializer, AnalysisDetailInputSerializer
from reception.models import Analysis
from rest_framework.response import Response
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from reception.models import Patient
from user.views.user_views import PartialPutMixin


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
        counts = {
            'kunlik_tahlil': Analysis.objects.filter(created_at__date=today).count(),
            'jami_tahlil': Analysis.objects.count(),
            'yangi_tahlil': Analysis.objects.filter(status=Analysis.Status.new, created_at__date=today).count(),
            'jarayondagi_tahlil': Analysis.objects.filter(status=Analysis.Status.in_progress,
                                                          created_at__date=today).count(),
            'yakunlangan_tahlil': Analysis.objects.filter(status=Analysis.Status.finished,
                                                          created_at__date=today).count(),
        }
        last_analysis = Analysis.objects.all().order_by('-created_at')[:10]
        counts['oxirgi_tahlillar'] = AnalysisSerializer(last_analysis, many=True, context={'request': request}).data
        return Response(counts, status=status.HTTP_200_OK)

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
    except Exception:
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
        "patient": {
            "name": patient.name,
            "last_name": patient.last_name
        }, "department_types": dept_types
    })


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
