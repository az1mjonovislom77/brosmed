from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from cashier.api.serializers import CashierSerializer
from cashier.selectors import cashiers as cashier_selectors
from cashier.services import cashier_service


@extend_schema(tags=['Cashier'])
class CashierViewSet(viewsets.ModelViewSet):
    queryset = cashier_selectors.get_all_patients()
    serializer_class = CashierSerializer
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({"detail": "patient_id yuborilishi shart."}, status=400)

        patient = cashier_selectors.get_patient_by_id(patient_id)
        if not patient:
            return Response({"detail": "Bunday bemor topilmadi."}, status=404)

        price = cashier_service.calculate_patient_price(patient)

        serializer = self.get_serializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        patient.total_amount = price
        patient = serializer.update(patient, serializer.validated_data)

        return Response(self.get_serializer(patient).data, status=200)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        data = cashier_selectors.get_cashier_stats()
        return Response(data, status=status.HTTP_200_OK)