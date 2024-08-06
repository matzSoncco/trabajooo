from django.db import models
from .Ppe import Ppe

class PpeStockUpdate(models.Model):
    ppe = models.ForeignKey(Ppe, on_delete=models.CASCADE, related_name='stock_updates')
    quantity = models.IntegerField(null=False)
    unitCost = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.ppe.name} - {self.quantity} @ {self.unitCost}"