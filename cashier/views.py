from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from reception.models import Patient
from .serializers import CashierSerializer
from django.utils import timezone


@extend_schema(tags=['Cashier'])
class CashierViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-id')
    serializer_class = CashierSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({"detail": "patient_id yuborilishi shart."}, status=400)

        try:
            patient = Patient.objects.get(id=int(patient_id))
        except Patient.DoesNotExist:
            return Response({"detail": "Bunday bemor topilmadi."}, status=404)

        if patient.user and getattr(patient.user, 'price', None):
            price = float(patient.user.price)
        elif patient.department_types and getattr(patient.department_types, 'price', None):
            price = float(patient.department_types.price)
        else:
            price = 0

        serializer = self.get_serializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        patient.total_amount = price
        patient = serializer.update(patient, serializer.validated_data)

        return Response(self.get_serializer(patient).data, status=200)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()

        # faqat bugungi confirmed bemorlar
        today_confirmed = Patient.objects.filter(
            payment_status=Patient.PaymentStatus.confirmed,
            updated_at__date=today
        )

        confirmed_patients = Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed)
        partial_patients = Patient.objects.filter(payment_status=Patient.PaymentStatus.partially_confirmed)

        all_unpaid_patients = Patient.objects.filter(
            payment_status__in=[Patient.PaymentStatus.pending, Patient.PaymentStatus.partially_confirmed]
        )

        total_confirmed = sum(float(p.paid_amount or 0) for p in confirmed_patients)
        total_partial = sum(float(p.partial_payment_amount or 0) for p in partial_patients)
        total_pending = sum(
            float(p.total_amount or 0) - (float(p.paid_amount or 0) + float(p.partial_payment_amount or 0))
            for p in all_unpaid_patients
        )

        today_income = sum(float(p.paid_amount or 0) for p in today_confirmed)

        data = {
            "bugungi_daromad": f"{today_income:,.0f} so'm",
            "tolangan": f"{total_confirmed:,.0f} so'm",
            "qisman_tolangan": f"{total_partial:,.0f} so'm",
            "kutilmoqda": f"{total_pending:,.0f} so'm",
            "jami_bemorlar": Patient.objects.count(),
        }
        return Response(data, status=status.HTTP_200_OK)
