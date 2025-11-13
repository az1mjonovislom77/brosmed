from rest_framework import serializers
from reception.models import Patient


class CashierSerializer(serializers.ModelSerializer):
    patient_id = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), write_only=True, required=False)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'department', 'department_types', 'patient_id', 'name', 'last_name', 'middle_name',
                  'gender', 'birth_date', 'phone_number', 'address', 'disease',
                  'payment_status', 'total_amount', 'paid_amount', 'partial_payment_amount', 'created_at']
        read_only_fields = ['id', 'user', 'department', 'name', 'last_name', 'middle_name', 'gender',
                            'birth_date', 'phone_number', 'address', 'disease', 'total_amount', 'paid_amount',
                            'department_types', 'created_at']

    def update(self, instance, validated_data):
        status = validated_data.get('payment_status', instance.payment_status)
        partial_paid = float(validated_data.get('partial_payment_amount', 0) or 0)

        total_amount = float(instance.total_amount or 0)
        paid_amount = float(instance.paid_amount or 0)
        partial_payment = float(instance.partial_payment_amount or 0)

        if partial_paid > 0 and status != Patient.PaymentStatus.confirmed:
            instance.partial_payment_amount = partial_payment + partial_paid
            instance.payment_status = Patient.PaymentStatus.partially_confirmed

        if status == Patient.PaymentStatus.confirmed:
            remaining = total_amount - paid_amount - partial_payment
            instance.paid_amount = paid_amount + partial_payment + remaining
            instance.partial_payment_amount = 0
            instance.payment_status = Patient.PaymentStatus.confirmed

        instance.save()
        return instance
