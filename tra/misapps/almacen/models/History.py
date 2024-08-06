from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class History(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey('content_type', 'object_name')
    object_name = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} - {self.content_type} - {self.timestamp}"
    
    @property
    def model_name(self):
        # Obtén el modelo asociado al tipo de contenido
        model = self.content_type.model_class()
        if model:
            return model.__name__
        return 'Desconocido'
    
    @property
    def additional_info(self):
        # Ajusta según el nombre del modelo
        model_name = self.model_name
        if model_name == 'Equipment':
            return 'Equipo'
        elif model_name == 'Tool':
            return 'Herramienta'
        elif model_name == 'Material':
            return 'Material'
        elif model_name == 'Ppe':
            return 'Equipo de protección personal'
        else:
            return 'Otro'
