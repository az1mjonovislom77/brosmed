import json
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from laboratory.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    AnalysisFullDetailSerializer, AnalysisDetailInputSerializer
from reception.models import Analysis
from rest_framework.response import Response
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from reception.models import Patient
from user.views.user_views import PartialPutMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math


class AnalysisPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.page_size
        total_pages = math.ceil(total / limit)

        return Response({
            "page": self.page.number,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "data": data,
        })


@extend_schema(tags=['Analysis'])
class AnalysisViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']
    pagination_class = AnalysisPagination

    def get_queryset(self):
        return (Analysis.objects
                .select_related('patient')
                .prefetch_related('department_types'))

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnalysisPostSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()

        qs = Analysis.objects.all()

        counts = qs.aggregate(
            jami_tahlil=Count('id'),
            kunlik_tahlil=Count('id', filter=Q(created_at__date=today)),
            yangi_tahlil=Count('id', filter=Q(status=Analysis.Status.new, created_at__date=today)),
            jarayondagi_tahlil=Count('id', filter=Q(status=Analysis.Status.in_progress, created_at__date=today)),
            yakunlangan_tahlil=Count('id', filter=Q(status=Analysis.Status.finished, created_at__date=today)),
        )

        last_analysis = (qs.select_related('patient').prefetch_related('department_types').order_by('-created_at')[:10])

        counts['oxirgi_tahlillar'] = AnalysisSerializer(last_analysis, many=True, context={'request': request}).data

        return Response(counts, status=status.HTTP_200_OK)

    @extend_schema(
        methods=['POST'],
        request=AnalysisSearchInputSerializer,
        responses={200: AnalysisSerializer(many=True)},
    )
    @action(detail=False, methods=['post'])
    def search(self, request):
        serializer = AnalysisSearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        search_value = serializer.validated_data['search']

        queryset = (
            self.get_queryset()
            .filter(
                Q(status__icontains=search_value)
                | Q(patient__name__icontains=search_value)
                | Q(patient__last_name__icontains=search_value)
                | Q(patient__middle_name__icontains=search_value)
                | Q(patient__phone_number__icontains=search_value)
                | Q(department_types__title__icontains=search_value)
            )
            .distinct()
            .only(
                'id',
                'status',
                'created_at',
                'patient__id',
                'patient__name',
                'patient__last_name',
                'patient__middle_name',
                'patient__phone_number',
            )
        )

        output = AnalysisSerializer(queryset, many=True, context={'request': request})
        return Response(output.data, status=status.HTTP_200_OK)


@csrf_exempt
def check_patient(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body)
        patient_id = body.get("patient_id")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not patient_id:
        return JsonResponse({"error": "patient_id required"}, status=400)

    try:
        patient = Patient.objects.get(id=int(patient_id))
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)

    full_name = " ".join(filter(None, [
        getattr(patient, "name", ""),
        getattr(patient, "last_name", ""),
        getattr(patient, "middle_name", "")
    ])).strip()

    if not full_name:
        full_name = f"patient_{patient.id}"

    return JsonResponse({
        "found": True,
        "patient": {
            "id": patient.id,
            "full_name": full_name,
            "name": getattr(patient, "name", ""),
            "last_name": getattr(patient, "last_name", ""),
            "middle_name": getattr(patient, "middle_name", "")
        }
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
