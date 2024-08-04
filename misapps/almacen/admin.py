from django.contrib import admin

# Register your models here.
from .models.Equipment import Equipment
from .models.Material import Material
from .models.Ppe import Ppe
from .models.Tool import Tool
from .models.Worker import Worker
from .models.History import History
from .models.Unit import Unit
from .models.PpeStockUpdate import PpeStockUpdate

admin.site.register(Equipment)
admin.site.register(Material)
admin.site.register(Ppe)
admin.site.register(Tool)
admin.site.register(Worker)
admin.site.register(History)
admin.site.register(Unit)
admin.site.register(PpeStockUpdate)