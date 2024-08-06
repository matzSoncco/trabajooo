from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Tool(models.Model):
    idTool = models.CharField(verbose_name=_('ID'), primary_key=True, editable=False, max_length=10)
    name = models.CharField(verbose_name=_('Nombre'), null=False, max_length=20)
    quantity = models.IntegerField(verbose_name=_('Cantidad'), validators=[MinValueValidator(0)], null=False, default=0)
    loanAmount = models.IntegerField(null=False, default=0)
    LEVELS = [
        (-1, 'Elija un nivel'),
        (1, 'Bajo'),
        (2, 'Medio'),
        (3, 'Mayor')
    ]
    level = models.IntegerField(verbose_name=_('Nivel'), null=False, choices=LEVELS, default=1)  # Default to a valid level
    stock = models.IntegerField(null=False, default=0)
    guideNumber = models.IntegerField(verbose_name=_('Número de Guía'), null=False, default=0)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    unitCost = models.DecimalField(default=0.0, null=False, max_digits=8, decimal_places=2)
    totalCost = models.DecimalField(default=0.0, null=False, max_digits=10, decimal_places=2, editable=False)

    def clean(self):
        if self.level == -1:
            raise ValidationError(_('Debe seleccionar un nivel válido.'))

    def save(self, *args, **kwargs):
        self.totalCost = self.unitCost * self.quantity
        if not self.idTool or not self.idTool.startswith('H-'):
            last_id = Tool.objects.all().order_by('-idTool').first()
            if last_id:
                try:
                    last_id_number = int(last_id.idTool.split('-')[1]) + 1
                except IndexError:
                    last_id_number = 1
            else:
                last_id_number = 1
            self.idTool = f'H-{last_id_number:04}'
        super(Tool, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s %s %s %s" %(self.idTool, self.name, self.quantity, self.level, self.stock)
