from django.db import models
from django.utils.translation import gettext_lazy as _
from .Unit import Unit

class Ppe(models.Model):
    idPpe = models.CharField(primary_key=True, editable=False, max_length=10)
    name = models.CharField(null=False, max_length=20, unique=True)
    quantity = models.IntegerField(null=False, default=0)
    unitCost = models.DecimalField(default=0.0, null=False, max_digits=8, decimal_places=2)
    totalCost = models.DecimalField(default=0.0, null=False, max_digits=10, decimal_places=2, editable=False)
    guideNumber = models.CharField(max_length=100)
    stock = models.IntegerField(null=False, default=0)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    duration = models.IntegerField(null=False, default=0, editable=True)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    creationDate = models.DateField(auto_now_add=False, blank=False, null=True)
    comments = models.TextField(null=True, max_length=120)

    def save(self, *args, **kwargs):
        # Calcula el totalCosto antes de guardar
        self.totalCost = self.unitCost * self.quantity
        
        if not self.idPpe or not self.idPpe.startswith('EPP-'):
            # Obtiene el número autoincrementable
            last_id = Ppe.objects.all().order_by('-idPpe').first()
            if last_id:
                # Intenta obtener el número del último idPpe
                try:
                    last_id_number = int(last_id.idPpe.split('-')[1]) + 1
                except IndexError:
                    # Si hay un IndexError, asigna 1 como el siguiente número
                    last_id_number = 1
            else:
                last_id_number = 1
            
            # Forma el nuevo ID con el formato EPP-numero
            self.idPpe = f'EPP-{last_id_number:04}'  # '04' asegura que siempre tenga 4 dígitos
        
        super(Ppe, self).save(*args, **kwargs)

    def calculate_average_cost(self, new_quantity, new_unit_cost):
        total_cost = (self.unitCost * self.quantity) + (new_unit_cost * new_quantity)
        total_quantity = self.quantity + new_quantity
        return total_cost / total_quantity

    def __str__(self):
        return f"{self.idPpe} {self.name} {self.quantity} {self.guideNumber} {self.unitCost} {self.totalCost} {self.stock}"