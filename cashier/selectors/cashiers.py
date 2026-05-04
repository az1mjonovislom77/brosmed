from reception.models import Patient
from django.utils import timezone

def get_all_patients():
    return Patient.objects.all().order_by('-id')

def get_patient_by_id(patient_id):
    try:
        return Patient.objects.get(id=int(patient_id))
    except Patient.DoesNotExist:
        return None

def get_cashier_stats():
    today = timezone.now().date()

    today_patients = Patient.objects.filter(created_at__date=today)
    bugungi_bemorlar_soni = today_patients.count()

    today_confirmed = Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed, updated_at__date=today)

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

    return {
        "bugungi_daromad": f"{today_income:,.0f} so'm",
        "tolangan": f"{total_confirmed:,.0f} so'm",
        "qisman_tolangan": f"{total_partial:,.0f} so'm",
        "kutilmoqda": f"{total_pending:,.0f} so'm",
        "bugungi_bemorlar": bugungi_bemorlar_soni,
        "jami_bemorlar": Patient.objects.count(),
    }
