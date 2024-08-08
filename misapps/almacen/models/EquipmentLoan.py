from django.db import models
from .Equipment import Equipment
from .Worker import Worker
from django.utils import timezone

class EquipmentLoan(models.Model):
    idEquipmentLoan = models.AutoField(primary_key=True, editable=False)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='equipment_loans', null=True)
    workerPosition = models.CharField(max_length=100, null=True)
    workerDni = models.CharField(max_length=8, null=True)
    loanDate = models.DateField(default=timezone.now)
    loanAmount = models.IntegerField(default=0)
    returnLoanDate = models.DateField(default=timezone.now)
    manager = models.CharField(max_length=100, default='')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True)
    workOrder = models.IntegerField(null=False, default=0)
    loanStatus = models.BooleanField(default=False, editable=True)

    @property
    def status(self):
        return "Devuelto" if self.loanStatus else "No devuelto"
    
    @status.setter
    def status(self, value):
        self.loanStatus = (value == "No devuelto")
        self.save()