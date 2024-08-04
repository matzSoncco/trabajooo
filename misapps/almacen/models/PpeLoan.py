from django.db import models
from .Ppe import Ppe
from .Worker import Worker
from django.utils import timezone
from datetime import timedelta

class PpeLoan(models.Model):
    idPpeLoan = models.AutoField(primary_key=True, editable=False)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='worker', null=True)
    workerPosition = models.CharField(max_length=100, null=True)
    workerDni = models.CharField(max_length=20, null=True)
    loanDate = models.DateField(default=timezone.now)
    expirationDate = models.DateField(editable=False)
    manager = models.CharField(max_length=20, default='')
    loanAmount = models.IntegerField(default=0)
    ppe = models.ForeignKey(Ppe, on_delete=models.CASCADE, null=True)
    confirmed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # Si es un nuevo préstamo
            # Calcula la fecha de expiración al momento de la creación
            ppe_duration = self.ppe.duration
            self.expirationDate = self.loanDate + timedelta(days=ppe_duration)
        super().save(*args, **kwargs)