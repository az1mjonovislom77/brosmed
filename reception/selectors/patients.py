from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from reception.models import Patient, Disease, Analysis, AnalysisResult


def get_all_patients():
    return Patient.objects.select_related('user', 'department_types').order_by('-created_at')


def get_patient_stats():
    today = timezone.now().date()
    one_year_ago = today - timedelta(days=365)

    qabul_qilinganlar = Patient.objects.filter().count()
    bugungi_bemorlar = Patient.objects.filter(created_at__date=today).count()
    erkaklar = Patient.objects.filter(gender=Patient.GenderChoice.MALE).count()
    ayollar = Patient.objects.filter(gender=Patient.GenderChoice.FEMALE).count()
    yangi_tugilganlar = Patient.objects.filter(birth_date__gte=one_year_ago).count()
    oxirgi_bemorlar = Patient.objects.select_related('user', 'department_types').order_by('-created_at')[:10]

    return {
        "qabul_qilinganlar": qabul_qilinganlar,
        "bugungi_bemorlar": bugungi_bemorlar,
        "erkaklar": erkaklar,
        "ayollar": ayollar,
        "yangi_tugilganlar": yangi_tugilganlar,
        'oxirgi_bemorlar': oxirgi_bemorlar
    }


def get_doctor_patients_and_diseases(user):
    patients = Patient.objects.filter(user=user).exclude(
        patient_status=Patient.PatientStatus.finished).select_related(
        'user', 'department_types').order_by('-created_at')
    diseases = Disease.objects.filter(user=user).select_related(
        'patient__user', 'patient__department_types', 'department', 'department_types', 'user').order_by('-id')
    return patients, diseases


def get_patient_by_id(patient_id):
    try:
        return Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return None


def get_analyses_for_patient(patient):
    return Analysis.objects.filter(patient=patient).select_related(
        'department_types').prefetch_related('analysisfile_set').order_by('-created_at')


def search_patients(search_query):
    return Patient.objects.filter(
        Q(name__icontains=search_query)
        | Q(last_name__icontains=search_query)
        | Q(middle_name__icontains=search_query)
        | Q(phone_number__icontains=search_query)
        | Q(passport__icontains=search_query)
        | Q(address__icontains=search_query)
    ).select_related('user', 'department_types').distinct()


def get_all_diseases():
    return Disease.objects.select_related(
        'patient__user', 'patient__department_types', 'department', 'department_types', 'user')


def get_diseases_by_patient_id(patient_id):
    return Disease.objects.filter(patient_id=patient_id).select_related(
        'patient__user', 'patient__department_types', 'department', 'department_types', 'user')


def get_analysis_export_data(patient_id, analysis_id):
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        return None, None, None, None

    analysis = Analysis.objects.filter(id=analysis_id, patient_id=patient_id).first()
    if not analysis:
        return patient, None, None, None

    next_analysis = Analysis.objects.filter(
        patient=patient,
        department_types=analysis.department_types,
        created_at__gt=analysis.created_at
    ).order_by("created_at").first()

    results_qs = AnalysisResult.objects.filter(
        patient=patient,
        result__department_types=analysis.department_types,
        created_at__gte=analysis.created_at
    ).select_related('result').order_by('-created_at')

    if next_analysis:
        results_qs = results_qs.filter(created_at__lt=next_analysis.created_at)

    return patient, analysis, next_analysis, results_qs
