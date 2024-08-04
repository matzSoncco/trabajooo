from django.db import models
from django.utils.translation import gettext_lazy as _
from .Equipment import Equipment
from .Tool import Tool
from .Material import Material
from .Worker import Worker
from django.utils import timezone

class Loan(models.Model):
    idLoan = models.AutoField(primary_key=True, editable=False)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, null=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True)
    workOrderCode = models.IntegerField(verbose_name=_('Código de Órden de Trabajo'), null=False, default=0)
    loanDate = models.DateField(verbose_name=_('Fecha de Entrega'), default=timezone.now)
    returnLoanDate = models.DateField(verbose_name=_('Fecha de Devolución'), default=timezone.now)
    loanStatus = models.BooleanField(default=False, editable=True)

    @property
    def status(self):
        return "Devuelto" if self.loanStatus else "No devuelto"
    
    @status.setter
    def status(self, value):
        self.loanStatus = (value == "No devuelto")
        self.save() 