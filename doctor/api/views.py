from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from doctor.api.serializers import ConsultationsSerializer, ConsultationDetailInputSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from user.serializers.user_serializers import UserCreateSerializer
from user.views.user_views import PartialPutMixin
from doctor.selectors import consultations as consultation_selectors


@extend_schema(tags=['Doctor'])
class DoctorAPIView(ListAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        department_id = self.kwargs.get('department_id')
        return consultation_selectors.get_doctors_by_department(department_id)


@extend_schema(tags=['Consultations'])
class ConsultationsViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = consultation_selectors.get_all_consultations()
    serializer_class = ConsultationsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats_data = consultation_selectors.get_consultation_stats(request.user)

        oxirgi_konsultatsiyalar = stats_data['oxirgi_konsultatsiyalar']

        data = {
            "jami_bemorlar": stats_data['jami_bemorlar'],
            "bugungi_bemorlar": stats_data['bugungi_bemorlar'],
            "kutayotgan": stats_data['kutayotgan'],
            "davolanayotgan": stats_data['davolanayotgan'],
            "sogaygan": stats_data['sogaygan'],
            "shifokorlar": stats_data['shifokorlar'],
            'oxirgi_konsultatsiyalar': (
                ConsultationsSerializer(oxirgi_konsultatsiyalar, many=True, context={'request': request}).data if
                oxirgi_konsultatsiyalar else None)
        }

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=['Consultations'])
class PatientConsultationsAPI(APIView):
    serializer_class = ConsultationDetailInputSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConsultationDetailInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient_id = serializer.validated_data['patient_id']

        patient = consultation_selectors.get_patient_by_id(patient_id)
        if not patient:
            return Response({"error": "Patient topilmadi"}, status=404)

        consultations = consultation_selectors.get_consultations_for_patient(patient)
        output = ConsultationsSerializer(consultations, many=True, context={"request": request})

        return Response(output.data, status=200)