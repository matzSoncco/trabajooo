from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models.Ppe import Ppe
from .models.PpeLoan import PpeLoan
from .models.Equipment import Equipment
from .models.Material import Material
from .models.Tool import Tool
from .models.Worker import Worker
from .models.Loan import Loan
from .models.Unit import Unit
from .models.ToolLoan import ToolLoan
from .models.PpeStockUpdate import PpeStockUpdate
from .models.EquipmentStockUpdate import EquipmentStockUpdate
from .models.ToolStockUpdate import ToolStockUpdate
from .models.MaterialStockUpdate import MaterialStockUpdate
from django.contrib.auth.models import User

class AdminLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(AdminLoginForm, self).__init__(*args, **kwargs)

    username = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese su nombre de usuario"
    }), max_length=150)

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "input",
        "type": "password",
        "placeholder": "Ingrese su contraseña"
    }))

    class Meta:
        model = User
        fields = ['username', 'password']


class AdminSignUpForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese sus nombres"
    }), max_length=150,)

    last_name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese sus apellidos"
    }), max_length=150,)

    username = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Cree su nombre de Usuario"
    }), max_length=150)

    email = forms.EmailField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "email",
        "placeholder": "Ingrese su correo"
    }), max_length=150)

    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "input",
        "type": "password",
        "placeholder": "Cree una contraseña"
    }))

    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        "class": "input",
        "type": "password",
        "placeholder": "Ingrese la contraseña nuevamente"
    }))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Hacer que este usuario sea un administrador
        if commit:
            user.save()
        return user

class CreatePpeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el nombre del EPP"
    }))

    new_unit = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Nueva unidad'
    }))

    class Meta:
        model = Ppe
        fields = ['name', 'unit', 'image']
        widgets = {
            'image': forms.FileInput(attrs={
                "class": "input",
                "type": "file",
            }),
            'unit': forms.Select(attrs={'class': 'select-unit'}),
        }

    def __init__(self, *args, **kwargs):
        super(CreatePpeForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['unit'].queryset = Unit.get_default_units()
        self.fields['unit'].empty_label = "Seleccione la unidad"
        
    def clean(self):
        cleaned_data = super().clean()
        new_unit = cleaned_data.get('new_unit')

        if new_unit:
            unit, created = Unit.objects.get_or_create(name=new_unit)
            cleaned_data['unit'] = unit

        print(f"Cleaned data: {cleaned_data}")  # Añade este print para depuración
        return cleaned_data

class PpeForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el nombre del EPP",
        "id": "id_name"
    }))

    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
        "id": "id_unitCost"
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
        "id": "id_stock"
    }))

    guideNumber = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese la el número de guía",
        "id": "id_guideNumber"
    }))
    
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "id": "id_quantity",
        "min": "1",
        "max": "99999"
    }))

    creationDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
        "id": "id_creationDate"
    }))
    class Meta:
        model = Ppe
        fields = ['name', 'unitCost', 'stock', 'unit', 'guideNumber', 'image', 'duration', 'creationDate', 'quantity']
        widgets = {
            'image': forms.FileInput(attrs={
                "class": "input",
                "type": "file",
            }),
            'unit': forms.Select(attrs={'class': 'select-unit'}),
        }

    def __init__(self, *args, **kwargs):
        super(PpeForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['unit'].queryset = Unit.get_default_units()
        self.fields['unit'].empty_label = "Select unit"
        
    def clean(self):
        cleaned_data = super().clean()
        new_unit = cleaned_data.get('new_unit')

        if new_unit:
            unit, created = Unit.objects.get_or_create(name=new_unit)
            cleaned_data['unit'] = unit

        return cleaned_data
    
class PpeStockUpdateForm(forms.ModelForm):
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "id": "id_quantity",
        "min": "1",
        "max": "99999"
    }))
    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
        "id": "id_unitCost"
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
        "id": "id_stock"
    }))
    class Meta:
        model = PpeStockUpdate
        fields = ['ppe', 'quantity', 'unitCost', 'stock']
    
class CreateEquipmentForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el nombre del Equipo"
    }))

    serialNumber = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el número de serie"
    }))
    
    level = forms.ChoiceField(choices=Equipment.LEVELS, widget=forms.Select(attrs={
        "class": "input"
    }))

    class Meta:
        model = Equipment
        fields = ['name', 'serialNumber', 'image', 'level']
        widgets = {
            'image': forms.FileInput(attrs={
                "class": "input",
                "type": "file",
            }),
        }

class EquipmentForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input',
        'type': 'text',
        'placeholder': 'Nombre del equipo'
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
    }))

    guideNumber = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el número de guía"
    }))

    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "min": "1",
        "max": "99999"
    }))

    creationDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    level = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "input"
    }))

    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
    }))

    class Meta:
        model = Equipment
        fields = ['name', 'level', 'stock', 'guideNumber', 'quantity', 'creationDate']

    def _init_(self, *args, **kwargs):
        super(EquipmentForm, self)._init_(*args, **kwargs)
        self.fields['image'].required = False

class EquipmentStockUpdateForm(forms.ModelForm):
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "id": "id_quantity",
        "min": "1",
        "max": "99999"
    }))
    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
        "id": "id_unitCost"
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
        "id": "id_stock"
    }))
    class Meta:
        model = EquipmentStockUpdate
        fields = ['equipment', 'quantity', 'unitCost', 'stock']

class CreateMaterialForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el nombre del Material"
    }))

    new_unit = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Nueva unidad'}))

    class Meta:
        model = Material
        fields = ['name', 'unit', 'image']
        widgets = {
            'image': forms.FileInput(attrs={
                "class": "input",
                "type": "file",
            }),
            'unit': forms.Select(attrs={'class': 'select-unit'}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateMaterialForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['unit'].queryset = Unit.get_default_units()
        self.fields['unit'].empty_label = "Seleccione la unidad"
        
    def clean(self):
        cleaned_data = super().clean()
        new_unit = cleaned_data.get('new_unit')

        if new_unit:
            unit, created = Unit.objects.get_or_create(name=new_unit)
            cleaned_data['unit'] = unit

        print(f"Cleaned data: {cleaned_data}")  # Añade este print para depuración
        return cleaned_data

class MaterialForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Nombre del material",
    }))

    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
    }))

    guideNumber = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el número de guía",
        "id": "id_guideNumber"
    }))
    
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "min": "1",
        "max": "99999"
    }))

    creationDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",        
    }))
    class Meta:
        model = Material
        fields = ['name', 'unitCost', 'stock', 'unit', 'guideNumber', 'image', 'creationDate', 'quantity']
        widgets = {
            'image': forms.FileInput(attrs={
                "class": "input",
                "type": "file",
            }),
            'unit': forms.Select(attrs={'class': 'select-unit'}),
        }

    def _init_(self, *args, **kwargs):
        super(MaterialForm, self)._init_(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['unit'].queryset = Unit.get_default_units()
        self.fields['unit'].empty_label = "Select unit"
        
    def clean(self):
        cleaned_data = super().clean()
        new_unit = cleaned_data.get('new_unit')

        if new_unit:
            unit, created = Unit.objects.get_or_create(name=new_unit)
            cleaned_data['unit'] = unit

        return cleaned_data
    
class MaterialStockUpdateForm(forms.ModelForm):
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "id": "id_quantity",
        "min": "1",
        "max": "99999"
    }))
    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
        "id": "id_unitCost"
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
        "id": "id_stock"
    }))
    class Meta:
        model = MaterialStockUpdate
        fields = ['material', 'quantity', 'unitCost', 'stock']

class CreateToolForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el nombre de la Herramienta"
    }))

    serialNumber = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el número de serie"
    }))
    
    level = forms.ChoiceField(choices=Equipment.LEVELS, widget=forms.Select(attrs={
        "class": "input"
    }))

    class Meta:
        model = Tool
        fields = ['name', 'serialNumber', 'image', 'level']
        widgets = {
            'image': forms.FileInput(attrs={
                "class": "input",
                "type": "file",
            }),
        }

class ToolForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input',
        'type': 'text',
        'placeholder': 'Nombre de la herramienta'
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
    }))

    guideNumber = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese el número de guía"
    }))

    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "min": "1",
        "max": "99999"
    }))

    creationDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    level = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "input"
    }))

    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
    }))

    class Meta:
        model = Equipment
        fields = ['name', 'level', 'stock', 'guideNumber', 'quantity', 'creationDate']

    def _init_(self, *args, **kwargs):
        super(ToolForm, self)._init_(*args, **kwargs)
        self.fields['image'].required = False

class ToolStockUpdateForm(forms.ModelForm):
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese la cantidad a añadir",
        "id": "id_quantity",
        "min": "1",
        "max": "99999"
    }))
    unitCost = forms.FloatField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el costo unitario",
        "id": "id_unitCost"
    }))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Ingrese el stock ideal",
        "id": "id_stock"
    }))
    class Meta:
        model = ToolStockUpdate
        fields = ['tool', 'quantity', 'unitCost', 'stock']

class ToolLoanSearchForm(forms.Form):
    work_order = forms.IntegerField(label='Orden de Trabajo', required=False)
    worker_dni = forms.CharField(label='DNI del Trabajador', max_length=8, required=False)

    def clean(self):
        cleaned_data = super().clean()
        work_order = cleaned_data.get('work_order')
        worker_dni = cleaned_data.get('worker_dni')

        if not work_order and not worker_dni:
            raise forms.ValidationError('Por favor, ingrese al menos un criterio de búsqueda.')

class WorkerForm(forms.ModelForm):
    dni = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Ingrese su número de DNI"
    }), max_length=8)

    workerStatus = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'class': 'input',
        'type': 'checkbox'
    }))

    class Meta:
        model = Worker
        fields = ['dni', 'name', 'surname', 'position', 'contractDate', 'workerStatus']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'type': 'text',
                'placeholder': 'Ingrese los nombres'
            }),
            'surname': forms.TextInput(attrs={
                'class': 'surname-input',
                'type': 'text',
                'placeholder': 'Ingrese los apellidos'
            }),
            'position': forms.TextInput(attrs={
                'class': 'input',
                'type': 'text',
                'placeholder': 'Ingrese su cargo'
            }),
            'contractDate': forms.DateInput(attrs={
                'class': 'input',
                'type': 'date'
            }),
        }
        
class PpeLoanForm(forms.ModelForm):
    ppe = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Epp a asignar...",
    }))

    loanDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    loanAmount = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Cantidad a asignar..."
    }))

    worker = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Nombre del trabajador",
    }))

    workerPosition = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Posición del trabajador",
        "readonly": "readonly",
    }))

    workerDni = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "DNI del trabajador",
    }))

    class Meta:
        model = PpeLoan
        fields = ['ppe' , 'loanDate', 'loanAmount', 'worker', 'workerPosition', 'workerDni']

class ToolLoanForm(forms.ModelForm):
    tool = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Herramienta a asignar...",
    }))

    loanDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    returnLoanDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    loanAmount = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Cantidad a asignar"
    }))

    workOrder = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Código de orden de trabajo"
    }))

    worker = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Nombre del trabajador",
    }))

    workerPosition = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Posición del trabajador",
        "readonly": "readonly",
    }))

    workerDni = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "DNI del trabajador",
    }))

    loanStatus = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        "class": "input",
        "type": "checkbox",
    }))

    class Meta:
        model = ToolLoan
        fields = ['tool' , 'loanDate', 'loanAmount', 'worker', 'workerPosition', 'workerDni', 'returnLoanDate', 'workOrder', 'loanStatus']

class EquipmentLoanForm(forms.ModelForm):
    equipment = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Equipo a asignar",
    }))

    loanDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    returnLoanDate = forms.DateField(widget=forms.DateInput(attrs={
        "class": "input",
        "type": "date",
    }))

    loanAmount = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Cantidad a asignar"
    }))

    workOrder = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "input",
        "type": "number",
        "placeholder": "Código de orden de trabajo"
    }))

    worker = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Nombre del trabajador",
    }))

    workerPosition = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "Posición del trabajador",
        "readonly": "readonly",
    }))

    workerDni = forms.CharField(widget=forms.TextInput(attrs={
        "class": "input",
        "type": "text",
        "placeholder": "DNI del trabajador",
    }))

    loanStatus = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        "class": "input",
        "type": "checkbox",
    }))

    class Meta:
        model = ToolLoan
        fields = ['tool' , 'loanDate', 'loanAmount', 'worker', 'workerPosition', 'workerDni', 'returnLoanDate', 'workOrder', 'loanStatus']