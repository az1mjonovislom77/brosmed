from rest_framework import serializers
from reception.models import Patient


class CashierPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'name', 'last_name', 'middle_name', 'gender', 'birth_date',
                  'phone_number', 'address', 'disease', 'payment_status', 'patient_status', 'partial_payment_amount']

    def validate(self, data):
        status = data.get('payment_status', None)
        amount = data.get('partial_payment_amount', None)

        if status == 'pc' and (amount is None or amount <= 0):
            raise serializers.ValidationError(
                "Qisman to'langan bo'lsa, partial_payment_amount kiritilishi kerak va 0 dan katta bo'lishi lozim."
            )
        if status != 'pc' and amount is not None:
            data['partial_payment_amount'] = None
        return data
