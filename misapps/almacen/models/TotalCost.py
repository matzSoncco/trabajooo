from django.db import models
from .Ppe import Ppe
from .Equipment import Equipment
from .Material import Material
from .Tool import Tool

class TotalCost(models.Model):
    totalCost = models.AutoField(primary_key=True, editable=False)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, null=True)
    loanDate = models.DateField(default=timezone.now)
    newLoanDate = models.DateField(default=timezone.now)
    manager = models.CharField(null=False, max_length=20, default='')