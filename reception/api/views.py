from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from laboratory.api.serializers import AnalysisByPatientInputSerializer, AnalysisNestSerializer
from laboratory.api.views import AnalysisPagination
from reception.api.serializers import PatientSerializer, PatientPostSerializer, PatientSearchInputSerializer, \
    DiseaseSerializer, DiseaseGetSerializers, ExportAnalysisSerializer
from user.views.user_views import PartialPutMixin
from drf_yasg.utils import swagger_auto_schema
from reception.selectors import patients as patient_selectors
from reception.services import export_service


@extend_schema(tags=['Patient'])
class PatientViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = patient_selectors.get_all_patients()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']
    pagination_class = AnalysisPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientPostSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats_data = patient_selectors.get_patient_stats()
        oxirgi_bemorlar_serialized = (
            PatientSerializer(stats_data['oxirgi_bemorlar'], many=True, context={'request': request}).data
            if stats_data['oxirgi_bemorlar'] else None
        )
        data = {
            "qabul_qilinganlar": stats_data['qabul_qilinganlar'],
            "bugungi_bemorlar": stats_data['bugungi_bemorlar'],
            "erkaklar": stats_data['erkaklar'],
            "ayollar": stats_data['ayollar'],
            "yangi_tugilganlar": stats_data['yangi_tugilganlar'],
            'oxirgi_bemorlar': oxirgi_bemorlar_serialized
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=['Patient'])
class PatientDoctorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patients, diseases = patient_selectors.get_doctor_patients_and_diseases(request.user)
        patient_data = PatientSerializer(patients, many=True).data
        disease_data = DiseaseGetSerializers(diseases, many=True).data

        return Response({
            "patients": patient_data,
            "diseases": disease_data
        })


@extend_schema(tags=['Patient'])
class PatientAnalysisAPIView(APIView):
    serializer_class = AnalysisByPatientInputSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AnalysisByPatientInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient_id = serializer.validated_data['patient_id']

        patient = patient_selectors.get_patient_by_id(patient_id)
        if not patient:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        analyses = patient_selectors.get_analyses_for_patient(patient)
        output = AnalysisNestSerializer(analyses, many=True, context={"request": request})
        return Response(output.data)


@extend_schema(tags=['Patient'], request=PatientSearchInputSerializer, responses=PatientSerializer(many=True))
class PatientSearchAPIView(APIView):
    serializers_class = PatientSearchInputSerializer
    pagination_class = AnalysisPagination

    def post(self, request):
        search = request.data.get("search", "")
        queryset = patient_selectors.search_patients(search)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PatientSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


@extend_schema(tags=['Disease'])
class DiseaseViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = patient_selectors.get_all_diseases()
    serializer_class = DiseaseSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DiseaseGetSerializers
        return super().get_serializer_class()


@extend_schema(tags=['Disease'], request=None, responses=DiseaseSerializer(many=True))
class PatientDiseasesAPIView(APIView):

    def get(self, request, patient_id):
        queryset = patient_selectors.get_diseases_by_patient_id(patient_id)
        serializer = DiseaseGetSerializers(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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

        patient, analysis, next_analysis, results_qs = patient_selectors.get_analysis_export_data(patient_id, analysis_id)

        if not patient:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        if not analysis:
            return Response({"error": "Analysis not found for this patient"}, status=status.HTTP_404_NOT_FOUND)

        return export_service.generate_analysis_pdf(patient, analysis, results_qs)
