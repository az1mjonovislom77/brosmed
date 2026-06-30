from django.db.models import Sum
from django.utils import timezone
from reception.models import Patient


def get_all_patients():
    return Patient.objects.all().order_by('-id')


def get_patient_by_id(patient_id):
    try:
        return Patient.objects.get(id=int(patient_id))
    except Patient.DoesNotExist:
        return None


def get_cashier_stats():
    today = timezone.now().date()

    bugungi_bemorlar_soni = Patient.objects.filter(created_at__date=today).count()

    today_income = Patient.objects.filter(
        payment_status=Patient.PaymentStatus.confirmed, updated_at__date=today
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    total_confirmed = Patient.objects.filter(
        payment_status=Patient.PaymentStatus.confirmed
    ).aggregate(total=Sum('paid_amount'))['total'] or 0

    total_partial = Patient.objects.filter(
        payment_status=Patient.PaymentStatus.partially_confirmed
    ).aggregate(total=Sum('partial_payment_amount'))['total'] or 0

    pending_data = Patient.objects.filter(
        payment_status__in=[Patient.PaymentStatus.pending, Patient.PaymentStatus.partially_confirmed]
    ).aggregate(
        total_sum=Sum('total_amount'),
        paid_sum=Sum('paid_amount'),
        partial_sum=Sum('partial_payment_amount'),
    )
    total_pending = (
        float(pending_data['total_sum'] or 0)
        - float(pending_data['paid_sum'] or 0)
        - float(pending_data['partial_sum'] or 0)
    )

    return {
        "bugungi_daromad": f"{float(today_income):,.0f} so'm",
        "tolangan": f"{float(total_confirmed):,.0f} so'm",
        "qisman_tolangan": f"{float(total_partial):,.0f} so'm",
        "kutilmoqda": f"{total_pending:,.0f} so'm",
        "bugungi_bemorlar": bugungi_bemorlar_soni,
        "jami_bemorlar": Patient.objects.count(),
    }
