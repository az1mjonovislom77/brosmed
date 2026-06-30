from django.db.models import Count, Q
from django.utils import timezone
from reception.models import Analysis, Patient

def get_base_analysis_queryset():
    return Analysis.objects.select_related("patient", "department_types").prefetch_related("analysisfile_set")

def get_stats_counts(qs, start, end):
    return qs.aggregate(
        jami_tahlil=Count("id"),
        kunlik_tahlil=Count("id", filter=Q(created_at__gte=start, created_at__lt=end)),
        yangi_tahlil=Count("id", filter=Q(status=Analysis.Status.new)),
        jarayondagi_tahlil=Count("id", filter=Q(status=Analysis.Status.in_progress)),
        yakunlangan_tahlil=Count("id", filter=Q(status=Analysis.Status.finished)),
    )

def get_last_analysis(qs):
    return (
        qs.select_related("patient", "department_types")
        .prefetch_related("analysisfile_set")
        .order_by("-created_at")[:10]
    )

def get_analysis_stats(request):
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timezone.timedelta(days=1)

    stats_qs = Analysis.objects.all()
    counts = get_stats_counts(stats_qs, start, end)
    list_qs = get_base_analysis_queryset()
    last_analysis_qs = get_last_analysis(list_qs)

    return counts, last_analysis_qs

def search_analyses(search_value):
    qs = get_base_analysis_queryset()
    return qs.filter(
        Q(status__icontains=search_value)
        | Q(patient__name__icontains=search_value)
        | Q(patient__last_name__icontains=search_value)
        | Q(patient__middle_name__icontains=search_value)
        | Q(patient__phone_number__icontains=search_value)
        | Q(department_types__title__icontains=search_value)
    ).distinct()

def get_patient_basic_info(patient_id):
    return Patient.objects.filter(id=patient_id).only("id", "name", "last_name", "middle_name").first()

def get_patient_by_id(patient_id):
    return Patient.objects.filter(id=patient_id).only("id").first()

def get_analysis_by_id_and_patient(analysis_id, patient):
    return (
        Analysis.objects.select_related("patient", "department_types")
        .prefetch_related("analysisfile_set")
        .filter(id=analysis_id, patient=patient)
        .first()
    )
