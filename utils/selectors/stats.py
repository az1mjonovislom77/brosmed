from django.db.models import Sum
from department.models import Department
from doctor.models import Consultations
from reception.models import Patient, Analysis
from datetime import date, timedelta


def get_department_stats(dep, start_date, end_date):
    patients = Patient.objects.filter(department=dep, created_at__date__range=(start_date, end_date))
    total_payment = patients.filter(payment_status=Patient.PaymentStatus.confirmed).aggregate(total=Sum('paid_amount'))[
                        'total'] or 0.0

    return {
        "department": dep.title,
        "jami_bemorlar": patients.count(),
        "konsultatsiyalar": Consultations.objects.filter(patient__department=dep,
                                                         created_at__date__range=(start_date, end_date)).count(),
        "tahlillar": Analysis.objects.filter(patient__department=dep,
                                             created_at__date__range=(start_date, end_date)).count(),
        "tolovlar": total_payment
    }


def get_overall_stats(start_date, end_date):
    total_payment = Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed,
                                           updated_at__date__range=(start_date, end_date)).aggregate(
        total=Sum('paid_amount'))['total'] or 0.0
    return {
        "start_date": start_date,
        "end_date": end_date,
        "jami_bemorlar": Patient.objects.filter(created_at__date__range=(start_date, end_date)).count(),
        "konsultatsiyalar": Consultations.objects.filter(created_at__date__range=(start_date, end_date)).count(),
        "tahlillar": Analysis.objects.filter(created_at__date__range=(start_date, end_date)).count(),
        "tolovlar": total_payment
    }


def get_stats_data(start_date, end_date):
    overall = get_overall_stats(start_date, end_date)
    departments = [get_department_stats(dep, start_date, end_date) for dep in Department.objects.all()]
    return {"umumiy": overall, "departments": departments}


def get_last_week_stats():
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    results = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        results.append({
            "day": day,
            "patients": Patient.objects.filter(created_at__date=day).count(),
            "consultations": Consultations.objects.filter(created_at__date=day).count(),
            "tahlillar": Analysis.objects.filter(created_at__date=day).count(),
            "tolovlar": Patient.objects.filter(payment_status=Patient.PaymentStatus.confirmed,
                                               updated_at__date=day).aggregate(total=Sum('paid_amount'))[
                            'total'] or 0.0})
    return results
