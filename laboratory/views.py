import json
from django.db.models import Count, Q, Sum, Case, When, IntegerField
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from laboratory.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    AnalysisFullDetailSerializer, AnalysisDetailInputSerializer
from django.core.cache import cache
from reception.models import Analysis, Patient
from user.views.user_views import PartialPutMixin


class AnalysisPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = (total + limit - 1) // limit

        return Response(
            {
                "page": self.page.number,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "data": data,
            }
        )


@extend_schema(tags=["Analysis"])
class AnalysisViewSet(viewsets.ModelViewSet, PartialPutMixin):
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = AnalysisPagination

    CACHE_KEY_STATS = "analysis:stats"
    CACHE_TTL = 60

    def get_queryset(self):
        return Analysis.objects.select_related("patient")

    def get_serializer_class(self):
        if self.action == "create":
            return AnalysisPostSerializer
        return self.serializer_class

    def _get_stats_counts(self, qs, start, end):
        return qs.aggregate(
            jami_tahlil=Count("id"),

            kunlik_tahlil=Sum(
                Case(
                    When(created_at__gte=start, created_at__lt=end, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),

            yangi_tahlil=Sum(
                Case(
                    When(
                        status=Analysis.Status.new,
                        created_at__gte=start,
                        created_at__lt=end,
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),

            jarayondagi_tahlil=Sum(
                Case(
                    When(
                        status=Analysis.Status.in_progress,
                        created_at__gte=start,
                        created_at__lt=end,
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),

            yakunlangan_tahlil=Sum(
                Case(
                    When(
                        status=Analysis.Status.finished,
                        created_at__gte=start,
                        created_at__lt=end,
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
        )

    def _get_last_analysis(self, qs):
        return qs.order_by("-created_at")[:10]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        cached = cache.get(self.CACHE_KEY_STATS)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        now = timezone.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timezone.timedelta(days=1)

        qs = self.get_queryset()

        counts = self._get_stats_counts(qs, start, end)

        last_analysis_qs = self._get_last_analysis(qs)

        counts["oxirgi_tahlillar"] = AnalysisSerializer(
            last_analysis_qs,
            many=True,
            context={"request": request},
        ).data

        cache.set(self.CACHE_KEY_STATS, counts, self.CACHE_TTL)

        return Response(counts, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["POST"],
        request=AnalysisSearchInputSerializer,
        responses={200: AnalysisSerializer(many=True)},
    )
    @action(detail=False, methods=["post"])
    def search(self, request):
        input_serializer = AnalysisSearchInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        search_value = input_serializer.validated_data["search"]

        qs = self.get_queryset().prefetch_related("department_types")

        queryset = qs.filter(
            Q(status__icontains=search_value)
            | Q(patient__name__icontains=search_value)
            | Q(patient__last_name__icontains=search_value)
            | Q(patient__middle_name__icontains=search_value)
            | Q(patient__phone_number__icontains=search_value)
            | Q(department_types__title__icontains=search_value)
        ).distinct()

        page = self.paginate_queryset(queryset)
        serializer = AnalysisSerializer(
            page if page is not None else queryset,
            many=True,
            context={"request": request},
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _invalidate_cache(self):
        cache.delete(self.CACHE_KEY_STATS)

    def perform_create(self, serializer):
        instance = serializer.save()
        self._invalidate_cache()
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_cache()
        return instance

    def perform_destroy(self, instance):
        self._invalidate_cache()
        instance.delete()


@csrf_exempt
def check_patient(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        patient_id = body.get("patient_id")
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not patient_id:
        return JsonResponse({"error": "patient_id required"}, status=400)

    patient = (Patient.objects.filter(id=patient_id).only("id", "name", "last_name", "middle_name").first())

    if not patient:
        return JsonResponse({"error": "Patient not found"}, status=404)

    full_name = " ".join(filter(None, [getattr(patient, "name", ""), getattr(patient, "last_name", ""),
                                       getattr(patient, "middle_name", "")])).strip()

    if not full_name:
        full_name = f"patient_{patient.id}"

    return JsonResponse(
        {
            "found": True,
            "patient": {
                "id": patient.id,
                "full_name": full_name,
                "name": getattr(patient, "name", ""),
                "last_name": getattr(patient, "last_name", ""),
                "middle_name": getattr(patient, "middle_name", ""),
            },
        }
    )


@extend_schema(tags=["Analysis"])
class AnalysisDetailByPatient(APIView):
    serializer_class = AnalysisDetailInputSerializer

    def post(self, request):
        serializer = AnalysisDetailInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient_id = serializer.validated_data["patient_id"]
        analysis_id = serializer.validated_data["analysis_id"]
        patient = (Patient.objects.filter(id=patient_id).only("id").first())

        if not patient:
            return Response({"error": "Patient topilmadi"}, status=404)

        analysis = (
            Analysis.objects.select_related("patient")
            .prefetch_related("department_types")
            .filter(id=analysis_id, patient=patient).first()
        )

        if not analysis:
            return Response({"error": "Analysis topilmadi yoki bu patientga tegishli emas"}, status=404)

        output = AnalysisFullDetailSerializer(analysis, context={"request": request})

        return Response(output.data, status=200)
