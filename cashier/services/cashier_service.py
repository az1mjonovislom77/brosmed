def calculate_patient_price(patient):
    if patient.user and getattr(patient.user, 'price', None):
        return float(patient.user.price)
    elif patient.department_types and getattr(patient.department_types, 'price', None):
        return float(patient.department_types.price)
    return 0