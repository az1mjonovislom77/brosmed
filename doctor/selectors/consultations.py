from doctor.models import Consultations
from reception.models import Patient
from user.models import User
from django.utils import timezone


def get_doctors_by_department(department_id):
    return User.objects.filter(role=User.UserRoles.DOCTOR, department_id=department_id)


def get_all_consultations():
    return Consultations.objects.all()


def get_consultation_stats(user):
    today = timezone.now().date()

    oxirgi_konsultatsiyalar = Consultations.objects.filter(user=user).order_by('-created_at')[:10]

    return {
        "jami_bemorlar": Patient.objects.filter(user=user).count(),
        "bugungi_bemorlar": Patient.objects.filter(created_at__date=today, user=user).count(),
        "kutayotgan": Patient.objects.filter(created_at__date=today,
                                             patient_status=Patient.PatientStatus.in_register,
                                             user=user).count(),
        "davolanayotgan": Patient.objects.filter(created_at__date=today,
                                                 patient_status=Patient.PatientStatus.treating,
                                                 user=user).count(),
        "sogaygan": Patient.objects.filter(user=user,
                                           patient_status=Patient.PatientStatus.recovered).count(),
        "shifokorlar": User.objects.filter(role=User.UserRoles.DOCTOR).count(),
        "oxirgi_konsultatsiyalar": oxirgi_konsultatsiyalar
    }


def get_patient_by_id(patient_id):
    try:
        return Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return None


def get_consultations_for_patient(patient):
    return Consultations.objects.filter(patient=patient).order_by('-created_at')
