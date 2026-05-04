from department.models import Department, DepartmentTypes, Result
from reception.models import AnalysisResult

def get_all_department_types():
    return DepartmentTypes.objects.all().order_by('id')

def get_all_departments():
    return Department.objects.all().order_by('id')

def get_all_results():
    return Result.objects.all().order_by('id')

def get_all_analysis_results():
    return AnalysisResult.objects.all().order_by('id')