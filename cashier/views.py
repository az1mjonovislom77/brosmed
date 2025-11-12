from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from cashier.serializers import CashierPaymentSerializer
from reception.models import Patient
from rest_framework.permissions import IsAuthenticated

from user.views import PartialPutMixin


@extend_schema(tags=['Cashier'])
class CashierViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = CashierPaymentSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(payment_status='p')
