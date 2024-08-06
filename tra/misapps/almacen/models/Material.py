from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from .Unit import Unit

class Material(models.Model):
    idMaterial = models.CharField(primary_key=True, editable=False, max_length=10)
    name = models.CharField(null=False, max_length=20)
    quantity = models.IntegerField(validators=[MinValueValidator(0)], null=False, default=0)
    loanAmount = models.IntegerField(null=False, default=0)
    stock = models.IntegerField(null=False, default=0)
    guideNumber = models.IntegerField(null=False, default=0)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    creationDate = models.DateField(auto_now_add=True, blank=False, null=True)
    unitCost = models.DecimalField(default=0.0, null=False, max_digits=8, decimal_places=2)
    totalCost = models.DecimalField(default=0.0, null=False, max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        print(f"Guardando material: {self.name}")
        self.totalCost = self.unitCost * self.quantity
        if not self.idMaterial or not self.idMaterial.startswith('M-'):
            # Obtiene el número autoincrementable
            last_id = Material.objects.all().order_by('-idMaterial').first()
            if last_id:
                # Intenta obtener el número del último idMaterial
                try:
                    last_id_number = int(last_id.idMaterial.split('-')[1]) + 1
                except IndexError:
                    # Si hay un IndexError, asigna 1 como el siguiente número
                    last_id_number = 1
            else:
                last_id_number = 1
            
            self.idMaterial = f'M-{last_id_number:04}'  # '04' asegura que siempre tenga 4 dígitos
        
        super(Material, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s %s %s" %(self.idMaterial, self.name, self.quantity, self.stock)