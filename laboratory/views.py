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
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = AnalysisPagination

    def get_queryset(self):
        return Analysis.objects.select_related("patient")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AnalysisPostSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["get"])
    def stats(self, request):
        cache_key = "analysis:stats"
        data = cache.get(cache_key)
        if data:
            return Response(data, status=status.HTTP_200_OK)

        now = timezone.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timezone.timedelta(days=1)

        qs = self.get_queryset()

        counts = qs.aggregate(
            jami_tahlil=Count("id"),

            kunlik_tahlil=Sum(
                Case(
                    When(created_at__gte=start, created_at__lt=end, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ),

            yangi_tahlil=Sum(
                Case(
                    When(
                        status=Analysis.Status.new,
                        created_at__gte=start,
                        created_at__lt=end,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),

            jarayondagi_tahlil=Sum(
                Case(
                    When(
                        status=Analysis.Status.in_progress,
                        created_at__gte=start,
                        created_at__lt=end,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),

            yakunlangan_tahlil=Sum(
                Case(
                    When(
                        status=Analysis.Status.finished,
                        created_at__gte=start,
                        created_at__lt=end,
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
        )

        # 🔹 LAST 10 (safe fields, no N+1)
        last_analysis_qs = qs.order_by("-created_at")[:10]

        counts["oxirgi_tahlillar"] = AnalysisSerializer(
            last_analysis_qs,
            many=True,
            context={"request": request}
        ).data

        cache.set(cache_key, counts, timeout=60)

        return Response(counts, status=status.HTTP_200_OK)

    # 🔹 SEARCH (optimized + pagination + controlled prefetch)
    @extend_schema(
        methods=["POST"],
        request=AnalysisSearchInputSerializer,
        responses={200: AnalysisSerializer(many=True)}
    )
    @action(detail=False, methods=["post"])
    def search(self, request):
        serializer = AnalysisSearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        search_value = serializer.validated_data["search"]

        qs = self.get_queryset().prefetch_related("department_types")

        queryset = (
            qs.filter(
                Q(status__icontains=search_value)
                | Q(patient__name__icontains=search_value)
                | Q(patient__last_name__icontains=search_value)
                | Q(patient__middle_name__icontains=search_value)
                | Q(patient__phone_number__icontains=search_value)
                | Q(department_types__title__icontains=search_value)
            )
            .distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AnalysisSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = AnalysisSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 🔹 CACHE INVALIDATION (fixed key)
    def perform_create(self, serializer):
        cache.delete("analysis:stats")
        serializer.save()

    def perform_update(self, serializer):
        cache.delete("analysis:stats")
        serializer.save()

    def perform_destroy(self, instance):
        cache.delete("analysis:stats")
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
