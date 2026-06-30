from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
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

    departments_qs = Department.objects.annotate(
        jami_bemorlar=Count(
            'patient',
            filter=Q(patient__created_at__date__range=(start_date, end_date)),
            distinct=True,
        ),
        tolovlar=Sum(
            'patient__paid_amount',
            filter=Q(
                patient__payment_status=Patient.PaymentStatus.confirmed,
                patient__created_at__date__range=(start_date, end_date),
            ),
        ),
        konsultatsiyalar=Count(
            'patient__consultations',
            filter=Q(patient__consultations__created_at__date__range=(start_date, end_date)),
            distinct=True,
        ),
        tahlillar=Count(
            'patient__analysis',
            filter=Q(patient__analysis__created_at__date__range=(start_date, end_date)),
            distinct=True,
        ),
    )

    departments = [
        {
            "department": dep.title,
            "jami_bemorlar": dep.jami_bemorlar,
            "konsultatsiyalar": dep.konsultatsiyalar,
            "tahlillar": dep.tahlillar,
            "tolovlar": float(dep.tolovlar or 0),
        }
        for dep in departments_qs
    ]
    return {"umumiy": overall, "departments": departments}


def get_last_week_stats():
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    patient_by_day = {
        row['day']: row['count']
        for row in Patient.objects.filter(created_at__date__range=(start_date, end_date))
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
    }

    payment_by_day = {
        row['day']: float(row['total'] or 0)
        for row in Patient.objects.filter(
            payment_status=Patient.PaymentStatus.confirmed,
            updated_at__date__range=(start_date, end_date),
        ).annotate(day=TruncDate('updated_at'))
        .values('day')
        .annotate(total=Sum('paid_amount'))
    }

    consultation_by_day = {
        row['day']: row['count']
        for row in Consultations.objects.filter(created_at__date__range=(start_date, end_date))
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
    }

    analysis_by_day = {
        row['day']: row['count']
        for row in Analysis.objects.filter(created_at__date__range=(start_date, end_date))
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
    }

    results = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        results.append({
            "day": day,
            "patients": patient_by_day.get(day, 0),
            "consultations": consultation_by_day.get(day, 0),
            "tahlillar": analysis_by_day.get(day, 0),
            "tolovlar": payment_by_day.get(day, 0.0),
        })
    return results
