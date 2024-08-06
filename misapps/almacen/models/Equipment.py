from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Equipment(models.Model):
    idEquipment = models.CharField(verbose_name=_('ID'), primary_key=True, editable=False, max_length=10)
    name = models.CharField(verbose_name=_('Nombre'), null=False, max_length=20)
    quantity = models.IntegerField(verbose_name=_('Cantidad'), null=False, default=0)
    loanAmount = models.IntegerField(null=False, default=0)
    LEVELS = [
        (-1, 'Elija un nivel'),
        (1, 'Bajo'),
        (2, 'Medio'),
        (3, 'Mayor')
    ]
    level = models.IntegerField(verbose_name=_('Nivel'), null=False, choices=LEVELS, default=-1)
    stock = models.IntegerField(verbose_name=_('Stock'), null=False, default=0)
    guideNumber = models.IntegerField(verbose_name=_('Número de Guía'), null=False, default=0)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    serialNumber = models.IntegerField(verbose_name=_('Número de Serie'), null=False, default=0)
    creationDate = models.DateField(verbose_name=_('Fecha de Creación'), default=timezone.now, blank=False, null=False)
    unitCost = models.DecimalField(default=0.0, null=False, max_digits=8, decimal_places=2)
    totalCost = models.DecimalField(default=0.0, null=False, max_digits=10, decimal_places=2, editable=False)
    
    def get_level_display(self):
        return dict(self.LEVELS).get(self.level, 'Desconocido')
    
    def clean(self):
        if self.level == -1:
            raise ValidationError(_('Debe seleccionar un nivel válido.'))

    def save(self, *args, **kwargs):
        self.totalCost = self.unitCost * self.quantity
        if not self.idEquipment or not self.idEquipment.startswith('E-'):
            # Obtiene el número autoincrementable
            last_id = Equipment.objects.all().order_by('-idEquipment').first()
            if last_id:
                # Intenta obtener el número del último idEquipment
                try:
                    last_id_number = int(last_id.idEquipment.split('-')[1]) + 1
                except IndexError:
                    # Si hay un IndexError, asigna 1 como el siguiente número
                    last_id_number = 1
            else:
                last_id_number = 1
            
            self.idEquipment = f'E-{last_id_number:04}'  # '04' asegura que siempre tenga 4 dígitos
        
        super(Equipment, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s %s %s %s" % (self.idEquipment, self.name, self.quantity, self.level, self.stock)
