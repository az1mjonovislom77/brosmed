import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from laboratory.api.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    AnalysisFullDetailSerializer, AnalysisDetailInputSerializer
from django.core.cache import cache
from user.views.user_views import PartialPutMixin
from laboratory.selectors import analyses as analysis_selectors


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
    CACHE_TTL = 300

    def get_queryset(self):
        return analysis_selectors.get_base_analysis_queryset()

    def get_serializer_class(self):
        if self.action == "create":
            return AnalysisPostSerializer
        return self.serializer_class

    @action(detail=False, methods=["get"])
    def stats(self, request):
        cached = cache.get(self.CACHE_KEY_STATS)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        counts, last_analysis_qs = analysis_selectors.get_analysis_stats(request)
        counts["oxirgi_tahlillar"] = AnalysisSerializer(last_analysis_qs, many=True, context={"request": request}).data

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
        queryset = analysis_selectors.search_analyses(search_value)

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

    patient = analysis_selectors.get_patient_basic_info(patient_id)

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
        
        patient = analysis_selectors.get_patient_by_id(patient_id)

        if not patient:
            return Response({"error": "Patient topilmadi"}, status=404)

        analysis = analysis_selectors.get_analysis_by_id_and_patient(analysis_id, patient)

        if not analysis:
            return Response({"error": "Analysis topilmadi yoki bu patientga tegishli emas"}, status=404)

        output = AnalysisFullDetailSerializer(analysis, context={"request": request})

        return Response(output.data, status=200)