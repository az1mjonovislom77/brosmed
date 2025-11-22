from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from laboratory.serializers import AnalysisByPatientInputSerializer, AnalysisNestSerializer
from reception.models import Patient, Analysis, Disease
from reception.serializers import PatientSerializer, PatientPostSerializer, PatientSearchInputSerializer, \
    DiseaseSerializer, DiseaseGetSerializers
from user.views import PartialPutMixin
from datetime import timedelta
from django.db.models import Q


@extend_schema(tags=['Patient'])
class PatientViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientPostSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()
        one_year_ago = today - timedelta(days=365)

        qabul_qilinganlar = Patient.objects.filter().count()
        bugungi_bemorlar = Patient.objects.filter(created_at__date=today).count()
        erkaklar = Patient.objects.filter(gender=Patient.GenderChoice.MALE).count()
        ayollar = Patient.objects.filter(gender=Patient.GenderChoice.FEMALE).count()
        yangi_tugilganlar = Patient.objects.filter(birth_date__gte=one_year_ago).count()
        oxirgi_bemorlar = Patient.objects.all().order_by('-created_at')[:10]

        data = {
            "qabul_qilinganlar": qabul_qilinganlar,
            "bugungi_bemorlar": bugungi_bemorlar,
            "erkaklar": erkaklar,
            "ayollar": ayollar,
            "yangi_tugilganlar": yangi_tugilganlar,
            'oxirgi_bemorlar': (PatientSerializer(oxirgi_bemorlar, many=True, context={'request': request}).data if
                                oxirgi_bemorlar else None)
        }

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=['Patient'])
class PatientDoctorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patients = Patient.objects.filter(user=request.user).exclude(
            patient_status=Patient.PatientStatus.finished).order_by('-created_at')

        diseases = Disease.objects.filter(user=request.user).order_by('-id')
        patient_data = PatientSerializer(patients, many=True).data
        disease_data = DiseaseSerializer(diseases, many=True).data

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

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=404)

        analyses = Analysis.objects.filter(patient=patient)
        output = AnalysisNestSerializer(analyses, many=True, context={"request": request})
        return Response(output.data)


@extend_schema(tags=['Patient'], request=PatientSearchInputSerializer, responses=PatientSerializer(many=True))
class PatientSearchAPIView(APIView):
    serializers_class = PatientSearchInputSerializer

    def post(self, request):
        search = request.data.get("search", "")

        queryset = Patient.objects.filter(
            Q(name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(middle_name__icontains=search)
            | Q(phone_number__icontains=search)
            | Q(passport__icontains=search)
            | Q(address__icontains=search)
        ).distinct()

        return Response(PatientSerializer(queryset, many=True).data)


@extend_schema(tags=['Disease'])
class DiseaseViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Disease.objects.all()
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
        queryset = Disease.objects.filter(patient_id=patient_id)
        serializer = DiseaseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
