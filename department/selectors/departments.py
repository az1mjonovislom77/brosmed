from department.models import Department, DepartmentTypes, Result
from reception.models import AnalysisResult

def get_all_department_types():
    return DepartmentTypes.objects.prefetch_related('result').order_by('id')

def get_all_departments():
    return Department.objects.prefetch_related('department_types__result').order_by('id')

def get_all_results():
    return Result.objects.prefetch_related('analysis_result').order_by('id')

def get_all_analysis_results():
    return AnalysisResult.objects.select_related('result', 'patient').order_by('id')