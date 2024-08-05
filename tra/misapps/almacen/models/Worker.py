from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Worker(models.Model):
    dni = models.IntegerField(primary_key=True, default=0)
    position = models.CharField(null=False, max_length=20, default=None)
    contractDate = models.DateField(default=timezone.now)
    name = models.CharField(null=False, max_length=20)
    surname = models.CharField(null=False, max_length=20)
    workerStatus = models.BooleanField(default=True, editable=True)

    def __str__(self):
        return "%s %s %s" %(self.dni, self.name, self.surname)