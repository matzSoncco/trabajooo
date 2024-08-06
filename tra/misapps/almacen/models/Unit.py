from django.db import models

class Unit(models.Model):
    name = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.name

    @classmethod
    def get_default_units(cls):
        default_units = [
            'kg', 'g', 'm', 'cm'
            # Agrega más unidades predeterminadas aquí
        ]
        for unit in default_units:
            cls.objects.get_or_create(name=unit)
        return cls.objects.all()