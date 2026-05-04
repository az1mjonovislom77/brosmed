from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user.views.user_views import PartialPutMixin
from utils.models import ClinicAbout
from utils.api.serializers import (ClinicAboutSerializer, ClinicStatsInputSerializer, ClinicStatsResponseSerializer)
from utils.selectors import stats as stats_selectors
from utils.services import export_service


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
        stats = stats_selectors.get_stats_data(start_date, end_date)
        output = ClinicStatsResponseSerializer(stats)
        return Response(output.data, status=200)


@extend_schema(tags=['Report'])
class ClinicLastWeekAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        results = stats_selectors.get_last_week_stats()
        return Response(results)


class ClinicStatsExportMixin:
    def get_stats(self, request):
        serializer = ClinicStatsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        return stats_selectors.get_stats_data(start_date, end_date)


@extend_schema(tags=['Report'], request=ClinicStatsInputSerializer, responses={200: None})
class ClinicStatsExcelAPIView(ClinicStatsExportMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = self.get_stats(request)
        return export_service.export_stats_to_excel(data)


@extend_schema(tags=['Report'], request=ClinicStatsInputSerializer, responses={200: None})
class ClinicStatsPDFAPIView(ClinicStatsExportMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = self.get_stats(request)
        return export_service.export_stats_to_pdf(data)