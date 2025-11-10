from django.db import models


class DepartmentTypes(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'department_types'
        verbose_name = 'Department Types'
        verbose_name_plural = 'Department Types'


class Department(models.Model):
    title = models.CharField(max_length=100)
    department_types = models.ManyToManyField(DepartmentTypes, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'department'
        verbose_name = 'Department'
        verbose_name_plural = 'Department'

