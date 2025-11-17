from django.db import models


class Department(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'department'
        verbose_name = 'Department'
        verbose_name_plural = 'Department'


class DepartmentTypes(models.Model):
    title = models.CharField(max_length=200)
    price = models.CharField(max_length=200, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name='department_types', null=True,
                                   blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'department_types'
        verbose_name = 'Department Types'
        verbose_name_plural = 'Department Types'


class Result(models.Model):
    department_types = models.ForeignKey(DepartmentTypes, null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name='result')
    title = models.CharField(null=True, blank=True, max_length=500)
    norma = models.CharField(null=True, blank=True, max_length=500)

    def __str__(self):
        return self.title


class AnalysisResult(models.Model):
    result = models.ForeignKey(Result, null=True, blank=True, on_delete=models.SET_NULL, related_name='analysis_result')
    analysis_result = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.analysis_result
