from django.shortcuts import render, redirect
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import datetime
import json
import logging
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models.Ppe import Ppe
from .models.PpeLoan import PpeLoan
from .models.ToolLoan import ToolLoan
from .models.Equipment import Equipment
from .models.Worker import Worker
from .models.Material import Material
from .models.Tool import Tool
from .models.History import History
from .models.Unit import Unit
from .models.PpeStockUpdate import PpeStockUpdate
from .forms import AdminSignUpForm, PpeForm, MaterialForm, WorkerForm, EquipmentForm, ToolForm, PpeLoanForm, Ppe, CreatePpeForm, CreateMaterialForm, CreateEquipmentForm, CreateToolForm, PpeStockUpdateForm, ToolLoanForm

logger = logging.getLogger(__name__)

# Create your views here.
def home(request):
    return render(request, 'home.html')

#DURACIÓN
@login_required
def set_duration(request):
    form = PpeForm()
    return render(request, 'show_duration_table.html', {'form': form})

def cost_summary_view(request):
    epp_items = Ppe.objects.all()
    tool_items = Tool.objects.all()
    equip_items = Equipment.objects.all()
    mat_items = Material.objects.all()

    for item in epp_items:
        item.save()
    for item in tool_items:
        item.save()
    for item in equip_items:
        item.save()
    for item in mat_items:
        item.save()

    all_items = list(epp_items) + list(tool_items) + list(equip_items) + list(mat_items)
    
    final_total_cost = sum(item.totalCost for item in all_items)
    total_ppe_cost = sum(item.totalCost for item in epp_items)
    total_tool_cost = sum(item.totalCost for item in tool_items)
    total_equip_cost = sum(item.totalCost for item in equip_items)
    total_mat_cost = sum(item.totalCost for item in mat_items)

    context = {
        'all_items': all_items,
        'finalTotalCost': final_total_cost,
        'totalPpeCost': total_ppe_cost,
        'totalToolCost': total_tool_cost,
        'totalEquipCost': total_equip_cost,
        'totalMatCost': total_mat_cost
    }

    return render(request, 'total_cost_table.html', context)

@login_required
def show_duration(request):
    query = request.GET.get('q', '')
    if query:
        epp = Ppe.objects.filter(name__icontains=query)
    else:
        epp = Ppe.objects.all()
    return render(request, 'table_duration_ppe.html', {'epp': epp, 'query': query})

@require_POST
def update_ppe_duration(request):
    ppe_id = request.POST.get('ppe_id')
    new_duration = request.POST.get('duration')
    
    ppe = get_object_or_404(Ppe, idPpe=ppe_id)
    ppe.duration = new_duration
    ppe.save()
    
    return JsonResponse({'success': True})

#PPE
@login_required
def PersonalProtectionEquipment(request):
    query = request.GET.get('q', '')
    if query:
        epp = Ppe.objects.filter(name__icontains=query)
    else:
        epp = Ppe.objects.all()
    
    context = {'epp': epp, 'query': query}
    return render(request, 'table_created_ppe.html', context)

def get_ppe_data(request):
    ppe_id = request.GET.get('id')
    ppe = get_object_or_404(Ppe, idPpe=ppe_id)
    data = {
        'guideNumber': ppe.guideNumber,
        'creationDate': ppe.creationDate,
        'name': ppe.name,
        'unitCost': ppe.unitCost,
        'quantity': ppe.quantity,
        'stock': ppe.stock
    }
    return JsonResponse(data)
@csrf_exempt
def save_all_ppe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            for item in data:
                ppe = Ppe.objects.get(name=item['name'])
                quantity = int(item['quantity'])
                unitCost = Decimal(item['unitCost'])
                stock = int(item['stock'])
                
                total_cost = (ppe.unitCost * Decimal(ppe.quantity)) + (unitCost * quantity)
                ppe.quantity += quantity
                ppe.unitCost = total_cost / ppe.quantity
                ppe.stock = stock
                ppe.save()
                
                PpeStockUpdate.objects.create(
                    ppe=ppe,
                    quantity=quantity,
                    unitCost=unitCost,
                    date=item['creationDate']
                )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'})

@login_required
def add_ppe_stock(request):
    if request.method == 'POST':
        form = PpeStockUpdateForm(request.POST)
        if form.is_valid():
            ppe_stock_update = form.save(commit=False)
            
            # Obtener el objeto Ppe relacionado
            ppe = Ppe.objects.get(idPpe=ppe_stock_update.ppe.idPpe)
            
            # Actualizar la cantidad
            ppe.quantity += ppe_stock_update.quantity
            
            # Calcular el nuevo costo unitario
            ppe.unitCost = ((ppe.unitCost * ppe.quantity) + (ppe_stock_update.unitCost * ppe_stock_update.quantity)) / (ppe.quantity + ppe_stock_update.quantity)
            
            # Actualizar el stock ideal
            ppe.stock = ppe_stock_update.stock
            
            # Guardar las actualizaciones
            ppe.save()
            ppe_stock_update.save()
            
            return redirect('add_ppe_stock')
    else:
        form = PpeStockUpdateForm()
    return render(request, 'add_ppe_stock.html', {'form': form})

@login_required
def total_cost_ppe(request):
    query = request.GET.get('q', '')
    if query:
        epp = Ppe.objects.filter(name__icontains=query)
    else:
        epp = Ppe.objects.all()
    total_cost_final = 0
    for item in epp:
        item.save()
        total_cost_final += item.totalCost
    print(f"Número de PPEs encontrados: {epp.count()}")  # Añade este print
    return render(request, 'total_ppe_cost_table.html', {'epp': epp, 'query': query, 'total_cost_final': total_cost_final})

login_required
def show_added_ppe(request):
    query = request.GET.get('q', '')
    if query:
        epp = Ppe.objects.filter(name__icontains=query)
    else:
        epp = Ppe.objects.all()
    print(f"Número de PPEs encontrados: {epp.count()}")  # Añade este print
    return render(request, 'table_added_ppe.html', {'epp': epp, 'query': query})
    
def ppe_total(request):
    ppes = Ppe.objects.all()  
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            ppe_id = request.POST.get('delete')
            ppe = get_object_or_404(Ppe, id=ppe_id)
            ppe.delete()
            messages.success(request, 'EPP eliminado exitosamente.')
            return redirect('ppe_total')

        if 'edit' in request.POST:
            ppe_id = request.POST.get('edit')
            ppe = get_object_or_404(Ppe, id=ppe_id)
            form = CreatePpeForm(request.POST, request.FILES, instance=ppe)
            if form.is_valid():
                form.save()
                messages.success(request, 'EPP actualizado exitosamente.')
                return redirect('ppe_total')
    
    form = CreatePpeForm()  # Inicializa el formulario para crear o editar
    return render(request, 'ppe_total.html', {'ppes': ppes, 'form': form})

@login_required
def create_ppe(request):
    if request.method == 'POST':
        form = CreatePpeForm(request.POST, request.FILES)

        new_unit_name = request.POST.get('new_unit')
        if new_unit_name:
            unit, created = Unit.objects.get_or_create(name=new_unit_name)
            post_data = request.POST.copy()
            post_data['unit'] = unit.id
            form = CreatePpeForm(post_data, request.FILES)
        
        if form.is_valid():
            ppe = form.save(commit=False)
            ppe.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(ppe),
                object_name=ppe.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'EPP creado exitosamente.')
            return redirect('create_ppe')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreatePpeForm()
    return render(request, 'create_ppe.html', {'form': form})

@csrf_exempt
@require_POST
def add_new_unit(request):
    try:
        data = json.loads(request.body)
        new_unit_name = data.get('new_unit')
        if new_unit_name:
            unit, created = Unit.objects.get_or_create(name=new_unit_name)
            if created:
                return JsonResponse({'success': True, 'unit': unit.name})
            else:
                return JsonResponse({'success': False, 'message': 'La unidad ya existe.'})
        return JsonResponse({'success': False, 'message': 'Nombre de la unidad no proporcionado.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Error al procesar la solicitud.'})

@login_required
def add_ppe(request):
    if request.method == 'POST':
        form = PpeForm(request.POST)
        if form.is_valid():
            # Obtener datos del formulario y convertirlos a los tipos correctos
            guideNumber = form.cleaned_data['guideNumber']
            creationDate = form.cleaned_data['creationDate']
            name = form.cleaned_data['name']
            unitCost = Decimal(form.cleaned_data['unitCost'])
            quantity = int(form.cleaned_data['quantity'])
            stock = int(form.cleaned_data['stock'])
            
            # Obtener o crear el objeto Ppe
            ppe, created = Ppe.objects.get_or_create(name=name)
            
            # Actualizar la cantidad y el costo unitario del Ppe
            total_cost = (ppe.unitCost * Decimal(ppe.quantity)) + (unitCost * quantity)
            total_quantity = ppe.quantity + quantity
            ppe.unitCost = total_cost / total_quantity
            ppe.quantity = total_quantity
            ppe.stock = stock
            ppe.save()
            
            # Crear el registro de actualización de stock
            PpeStockUpdate.objects.create(
                ppe=ppe,
                quantity=quantity,
                unitCost=unitCost,
                date=creationDate
            )
            
            return redirect('add_ppe')
    else:
        form = PpeForm()
    return render(request, 'add_ppe.html', {'form': form})

@login_required
def delete_ppe(request, ppe_name):
    if request.method == 'DELETE':
        ppe = get_object_or_404(Ppe, name=ppe_name)
        ppe.delete()
        History.objects.create(
            content_type=ContentType.objects.get_for_model(ppe),
            object_name=ppe.name, 
            action='Deleted',
            user=request.user,
            timestamp=timezone.now()
        )
        return redirect('ppe_total')

@login_required
def modify_ppe(request, name):
    ppe = get_object_or_404(Ppe, name=name)

    if request.method == 'POST':
        form = CreatePpeForm(request.POST, request.FILES, instance=ppe)

        new_unit_name = request.POST.get('new_unit')
        if new_unit_name:
            unit, created = Unit.objects.get_or_create(name=new_unit_name)
            post_data = request.POST.copy()
            post_data['unit'] = unit.id
            form = CreatePpeForm(post_data, request.FILES, instance=ppe)
        
        if form.is_valid():
            ppe = form.save(commit=False)
            ppe.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(ppe),
                object_name=ppe.name, 
                action='Modified',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'EPP modificado exitosamente.')
            return redirect('ppe_total')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreatePpeForm(instance=ppe)

    return render(request, 'modify_ppe.html', {'form': form, 'ppe': ppe})

@login_required 
def total_ppe_stock(request):
    total_stock = Ppe.objects.aggregate(Sum('stock'))['stock__sum'] or 0
    return JsonResponse({'total_stock': total_stock})

#EQUIMENT
def equipment_total(request):
    equipments = Equipment.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            equipment_id = request.POST.get('delete')
            equipment = get_object_or_404(Equipment, id=equipment_id)
            equipment.delete()
            messages.success(request, 'Equipo eliminado exitosamente.')
            return redirect('equipment_total')

        if 'edit' in request.POST:
            equipment_id = request.POST.get('edit')
            equipment = get_object_or_404(Equipment, id=equipment_id)
            form = CreateEquipmentForm(request.POST, request.FILES, instance=equipment)
            if form.is_valid():
                form.save()
                messages.success(request, 'Equipo actualizado exitosamente.')
                return redirect('equipment_total')
    
    form = CreateEquipmentForm()  # Inicializa el formulario para crear o editar
    return render(request, 'equipment_total.html', {'equipments': equipments, 'form': form})
@login_required
def equipment_list(request):
    query = request.GET.get('q')
    if query:
        equipment = Equipment.objects.filter(name__icontains=query)
    else:
        equipment = Equipment.objects.all()
    return render(request, 'equipment_list.html', {'equipment': equipment, 'query': query})

@login_required
def total_cost_equip(request):
    query = request.GET.get('q')
    if query:
        equipment = Equipment.objects.filter(name__icontains=query)
    else:
        equipment = Equipment.objects.all()
    total_cost_final = 0
    for item in equipment:
        item.save()
        total_cost_final += item.totalCost
    return render(request, 'total_equip_cost_table.html', {'equipment': equipment, 'query': query, 'total_cost_final': total_cost_final})

@login_required
def create_equipment(request):
    if request.method == 'POST':
        form = CreateEquipmentForm(request.POST, request.FILES)
        
        if form.is_valid():
            equipment = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(equipment),
                object_name=equipment.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )
            messages.success(request, 'Equipo creado exitosamente.')
            return redirect('create_equipment')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreateEquipmentForm()
    return render(request, 'create_equipment.html', {'form': form})

@login_required
def delete_equipment(request, equipment_name):
    if request.method == 'POST':
        equipment = get_object_or_404(Equipment, name=equipment_name)
        equipment.delete()
        History.objects.create(
            content_type=ContentType.objects.get_for_model(equipment),
            object_name=equipment.name, 
            action='Deleted',
            user=request.user,
            timestamp=timezone.now()
        )
        return redirect('equipment_total')

@login_required
def modify_equipment(request, name):
    equipment = get_object_or_404(Equipment, name=name)
    if request.method == 'POST':
        form = CreateEquipmentForm(request.POST, request.FILES, instance=equipment)
        
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(equipment),
                object_name=equipment.name, 
                action='Modified',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'Equipo modificado exitosamente.')
            return redirect('equipment_total')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreateEquipmentForm(instance=equipment)

    return render(request, 'modify_equipment.html', {'form': form, 'equipment': equipment})

login_required
def total_equipment_stock(request):
    total_stock = Equipment.objects.aggregate(Sum('stock'))['stock__sum'] or 0
    return JsonResponse({'total_stock': total_stock})

#MATERIAL
def material_total(request):
    materials = Material.objects.all()
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            material_id = request.POST.get('delete')
            material = get_object_or_404(Material, id=material_id)
            material.delete()
            messages.success(request, 'Material eliminado exitosamente.')
            return redirect('material_total')

        if 'edit' in request.POST:
            material_id = request.POST.get('edit')
            material = get_object_or_404(Material, id=material_id)
            form = CreateMaterialForm(request.POST, request.FILES, instance=material)
            if form.is_valid():
                form.save()
                messages.success(request, 'Material actualizado exitosamente.')
                return redirect('material_total')
    
    form = CreateMaterialForm()  # Inicializa el formulario para crear o editar
    return render(request, 'material_total.html', {'materials': materials, 'form': form})
@login_required
def material_list(request):
    query = request.GET.get('q')
    if query:
        materials = Material.objects.filter(name__icontains=query)
    else:
        materials = Material.objects.all()
    return render(request, 'material_list.html', {'materials': materials, 'query': query})

@login_required
def create_material(request):
    if request.method == 'POST':
        form = CreateMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(material),
                object_name=material.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )
            print(f"Material creado: {material.idMaterial}")
            print(f"Datos del POST: {request.POST}")
            messages.success(request, 'Material creado exitosamente.')
            return redirect('create_material')
        else:
            print("Formulario no válido")
            print(form.errors)
    else:
        form = CreateMaterialForm()
    return render(request, 'create_material.html', {'form': form})

@login_required
def total_cost_material(request):
    query = request.GET.get('q')
    if query:
        materials = Material.objects.filter(name__icontains=query)
    else:
        materials = Material.objects.all()
    total_cost_final = 0
    for item in materials:
        item.save()
        total_cost_final += item.totalCost
    return render(request, 'total_mat_cost_table.html', {'materials': materials, 'query': query, 'total_cost_final': total_cost_final})

@login_required
def add_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('material_list')
    else:
        form = MaterialForm()
    return render(request, 'create_material.html', {'form': form})

@login_required
def delete_material(request, material_name):
    if request.method == 'POST':
        material = get_object_or_404(Ppe, name=material_name)
        material.delete()
        History.objects.create(
            content_type=ContentType.objects.get_for_model(material),
            object_name=material.name, 
            action='Deleted',
            user=request.user,
            timestamp=timezone.now()
        )
        return redirect('material_total')

@login_required   
def modify_material(request, material_name):
    material = get_object_or_404(Material, name=material_name)

    if request.method == 'POST':
        form = CreateMaterialForm(request.POST, request.FILES, instance=material)

        new_unit_name = request.POST.get('new_unit')
        if new_unit_name:
            unit, created = Unit.objects.get_or_create(name=new_unit_name)
            post_data = request.POST.copy()
            post_data['unit'] = unit.id
            form = CreateMaterialForm(post_data, request.FILES, instance=material)
        
        if form.is_valid():
            material = form.save(commit=False)
            material.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(material),
                object_name=material.name, 
                action='Modified',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'Material modificado exitosamente.')
            return redirect('material_total')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreateMaterialForm(instance=material)

    return render(request, 'modify_material.html', {'form': form, 'material': material})

@login_required 
def total_material_stock(request):
    total_stock = Material.objects.aggregate(Sum('stock'))['stock__sum'] or 0
    return JsonResponse({'total_stock': total_stock})

#TOOLS
def tool_total(request):
    tools = Tool.objects.all()  
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            tool_id = request.POST.get('delete')
            tool = get_object_or_404(Tool, idTool=tool_id)
            tool.delete()
            messages.success(request, 'Herramienta eliminada exitosamente.')
            return redirect('tool_total')

        if 'edit' in request.POST:
            tool_id = request.POST.get('edit')
            tool = get_object_or_404(Tool, idTool=tool_id)
            form = CreateToolForm(request.POST, request.FILES, instance=tool)
            if form.is_valid():
                form.save()
                messages.success(request, 'Herramienta actualizada exitosamente.')
                return redirect('tool_total')
    
    form = CreateToolForm()  # Inicializa el formulario para crear o editar
    return render(request, 'tool_total.html', {'tools': tools, 'form': form})

@login_required
def tool_list(request):
    query = request.GET.get('q')
    if query:
        tools = Tool.objects.filter(name__icontains=query)
    else:
        tools = Tool.objects.all()
    return render(request, 'tool_list.html', {'tools': tools, 'query': query})

@login_required
def total_cost_tool(request):
    query = request.GET.get('q', '')
    if query:
        tools = Tool.objects.filter(name__icontains=query)
    else:
        tools = Tool.objects.all()
    total_cost_final = 0
    for item in tools:
        item.save()
        total_cost_final += item.totalCost
    return render(request, 'total_tool_cost_table.html', {'tools': tools, 'query': query, 'total_cost_final': total_cost_final})

@login_required
def create_tool(request):
    if request.method == 'POST':
        form = CreateToolForm(request.POST, request.FILES)
        if form.is_valid():
            tool = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(tool),
                object_name=tool.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )
            messages.success(request, 'Herramienta guardada exitosamente.')
            return redirect('create_tool')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreateToolForm()
    return render(request, 'create_tool.html', {'form': form})

@login_required
def delete_tool(request, tool_name):
    if request.method == 'POST':
        tool = get_object_or_404(Ppe, name=tool_name)
        tool.delete()
        History.objects.create(
            content_type=ContentType.objects.get_for_model(tool),
            object_name=tool.name, 
            action='Deleted',
            user=request.user,
            timestamp=timezone.now()
        )
        return redirect('tool_total')

@login_required
def modify_tool(request, name):
    tool = get_object_or_404(Tool, name=name)
    if request.method == 'POST':
        form = CreateToolForm(request.POST, request.FILES, instance=tool)
        
        if form.is_valid():
            tool = form.save(commit=False)
            tool.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(tool),
                object_name=tool.name, 
                action='Modified',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'Herramienta modificado exitosamente.')
            return redirect('tool_total')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreateToolForm(instance=tool)

    return render(request, 'modify_tool.html', {'form': form, 'tool': tool})

login_required
def total_tool_stock(request):
    total_stock = Tool.objects.aggregate(Sum('stock'))['stock__sum'] or 0
    return JsonResponse({'total_stock': total_stock})

#WORKER
@login_required
def worker_list(request):
    query = request.GET.get('q', '')
    if query:
        workers = Worker.objects.filter(name__icontains=query) | \
                  Worker.objects.filter(surname__icontains=query) | \
                  Worker.objects.filter(dni__icontains=query) | \
                  Worker.objects.filter(position__icontains=query)
    else:
        workers = Worker.objects.all().order_by('-contractDate')
    return render(request, 'worker_list.html', {'workers': workers, 'query': query})

@login_required
def create_worker(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(worker),
                object_name=worker.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )
            return JsonResponse({'success': True, 'message': 'Trabajador creado con éxito'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = WorkerForm()
    return render(request, 'create_worker.html', {'form': form})

@login_required
def delete_worker(request, id):
    workers = get_object_or_404(Worker, dni=id)

    if request.method == 'POST':
        workers.delete()
        return redirect('worker_list')
    else:
        return render(request, 'delete_worker.html', {'workers': workers})
    
@login_required
def modify_worker(request, id):
    workers = get_object_or_404(Worker, dni=id)
    form = WorkerForm(instance=workers)

    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=workers)
        if form.is_valid():
            form.save()
            return redirect('worker_list')
    else:
        return render(request, 'modify_worker.html', {'form': form})

#TOOLLOAN
login_required
def add_tool_loan(request):
    tools = Tool.objects.all()
    if request.method == 'POST':
        form = ToolLoanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo de herramienta añadido con éxito.')
            return redirect('add_tool_loan')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = ToolLoanForm()
    
    return render(request, 'add_tool_loan.html', {'form': form, 'tools': tools})
    
@require_http_methods(["GET", "POST"])
def tool_loan_form(request):
    if request.method == 'POST':
        form = ToolLoanForm(request.POST)
        if form.is_valid():
            # No guardamos el formulario aún, solo obtenemos los datos limpios
            cleaned_data = form.cleaned_data
            
            # Obtenemos el trabajador
            worker_name = cleaned_data['worker']
            try:
                worker = Worker.objects.get(name=worker_name)
            except Worker.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Trabajador no encontrado'
                }, status=400)

            # Obtenemos el EPP
            tool_name = cleaned_data['tool']
            try:
                tool = Tool.objects.get(name=tool_name)
            except Tool.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'EPP no encontrado'
                }, status=400)

            # Construimos la respuesta JSON
            response_data = {
                'success': True,
                'data': {
                    'worker': worker.name,
                    'workerPosition': cleaned_data['workerPosition'],
                    'workerDni': worker.dni,
                    'loanStatus': tool.loanStatus,
                    'loanDate': cleaned_data['loanDate'].strftime('%Y-%m-%d'),
                    'returnLoanDate': cleaned_data['returnLoanDate'].strftime('%Y-%m-%d'),
                    'tool': tool.name,
                    'quantity': cleaned_data['loanAmount'],
                    # Agrega aquí cualquier otro campo que necesites
                }
            }
            return JsonResponse(response_data)
        else:
            # Si el formulario no es válido, devolvemos los errores
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    else:
        # Para solicitudes GET, simplemente devolvemos un mensaje
        return JsonResponse({
            'success': True,
            'message': 'Use POST to submit form data'
        })
    
@require_GET
def check_tool_availability(request):
    tool_name = request.GET.get('tool_name')

    try:
        tool = Tool.objects.get(name=tool_name)
        quantity = tool.quantity

        can_assign = quantity > 0
        message = '' if can_assign else 'No hay suficiente cantidad disponible.'

        response = {
            'can_assign': can_assign,
            'available': quantity,
            'message': message
        }
    except Tool.DoesNotExist:
        response = {
            'can_assign': False,
            'available': 0,
            'message': 'Herramienta no encontrada.'
        }

    return JsonResponse(response)

def process_tool_loan(loan):
    tool_name = loan.get('name')
    quantity = int(loan.get('quantity', 0))
    
    worker_data = loan.get('worker', {})
    worker_name = worker_data.get('name')
    worker_dni = worker_data.get('dni')
    worker_position = worker_data.get('position')
    
    loan_date_str = loan.get('loanDate')
    return_date_str = loan.get('returnLoanDate')
    loan_status = loan.get('loanStatus')
    
    if not tool_name:
        return {'success': False, 'error': 'Falta el nombre de la herramienta'}
    
    if not loan_date_str:
        return {'success': False, 'error': 'Falta la fecha de entrega'}
    
    if not return_date_str:
        return {'success': False, 'error': 'Falta la fecha de devolución'}
    
    try:
        loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'error': 'Formato de fecha de entrega inválido'}
    
    try:
        return_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'error': 'Formato de fecha de devolución inválido'}
    
    try:
        tool = Tool.objects.get(name=tool_name)
        worker = Worker.objects.get(dni=worker_dni)
    except Tool.DoesNotExist:
        return {'success': False, 'error': f'Herramienta {tool_name} no encontrada'}
    except Worker.DoesNotExist:
        return {'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'}

    # Verificar cantidad disponible
    if tool.quantity < quantity:  # Cambiado de ppe.quantity a ppe.stock
        return {'success': False, 'error': f'Cantidad insuficiente disponible para {tool_name}'}

    # Procesar el préstamo
    new_loan = ToolLoan(
        worker=worker,
        workerPosition=worker_position,
        workerDni=worker_dni,
        loanDate=loan_date,
        loanAmount=quantity,
        tool=tool,
        loanStatus=loan_status,
    )
    new_loan.save()
    tool.quantity -= quantity  # Actualizar stock en lugar de quantity
    tool.save()
    return {'success': True, 'message': f'Nuevo préstamo creado para {tool_name} asignado a {worker.name}'}

@csrf_exempt
def confirm_tool_loan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Datos recibidos:", json.dumps(data, indent=2))  # Depuración mejorada
            tool_loans = data.get('tool_loans', [])
            responses = []

            for loan in tool_loans:
                try:
                    response = process_tool_loan(loan)
                    responses.append(response)
                except Exception as e:
                    print(f"Error procesando préstamo: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
                    responses.append({'success': False, 'error': str(e)})

            if any(not r['success'] for r in responses):
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            return JsonResponse({'success': True, 'messages': responses})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)
        except Exception as e:
            print(f"Error general: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

#PPELOAN
@login_required
def ppe_loan_list(request):
    query = request.GET.get('q')
    if query:
        ppe_loans = PpeLoan.objects.filter(worker__name_icontains=query)
    else:
        ppe_loans = PpeLoan.objects.all()
    print(f"Número de préstamos: {ppe_loans.count()}")
    print(f"Préstamos: {list(ppe_loans)}")
    return render(request, 'ppe_loan_list.html', {'ppe_loans': ppe_loans, 'query': query})

@login_required
def add_ppe_loan(request):
    ppes = Ppe.objects.all()
    if request.method == 'POST':
        form = PpeLoanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_ppe_loan')
    else:
        form = PpeLoanForm()
    return render(request, 'add_ppe_loan.html', {'form': form, 'ppes': ppes})

@require_http_methods(["GET", "POST"])
def ppe_loan_form(request):
    if request.method == 'POST':
        form = PpeLoanForm(request.POST)
        if form.is_valid():
            # No guardamos el formulario aún, solo obtenemos los datos limpios
            cleaned_data = form.cleaned_data
            
            # Obtenemos el trabajador
            worker_name = cleaned_data['worker']
            try:
                worker = Worker.objects.get(name=worker_name)
            except Worker.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Trabajador no encontrado'
                }, status=400)

            # Obtenemos el EPP
            ppe_name = cleaned_data['ppe']
            try:
                ppe = Ppe.objects.get(name=ppe_name)
            except Ppe.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'EPP no encontrado'
                }, status=400)

            # Construimos la respuesta JSON
            response_data = {
                'success': True,
                'data': {
                    'worker': worker.name,
                    'workerPosition': cleaned_data['workerPosition'],
                    'workerDni': worker.dni,
                    'loanDate': cleaned_data['loanDate'].strftime('%Y-%m-%d'),
                    'ppe': ppe.name,
                    'quantity': cleaned_data['loanAmount'],
                    # Agrega aquí cualquier otro campo que necesites
                }
            }
            return JsonResponse(response_data)
        else:
            # Si el formulario no es válido, devolvemos los errores
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    else:
        # Para solicitudes GET, simplemente devolvemos un mensaje
        return JsonResponse({
            'success': True,
            'message': 'Use POST to submit form data'
        })

def worker_autocomplete(request):
    if 'term' in request.GET:
        qs = Worker.objects.filter(name__icontains=request.GET.get('term'))
        names = list(qs.values_list('name', flat=True))
        return JsonResponse(names, safe=False)
    return JsonResponse([], safe=False)

def dni_autocomplete(request):
    if 'term' in request.GET:
        qs = Worker.objects.filter(dni__icontains=request.GET.get('term'))
        dnis = list(qs.values_list('dni', flat=True))
        return JsonResponse(dnis, safe=False)
    return JsonResponse([], safe=False)

def worker_details(request):
    if 'worker_name' in request.GET:
        worker = Worker.objects.get(name=request.GET.get('worker_name'))
        return JsonResponse({
            'name': worker.name,
            'dni': worker.dni,
            'position': worker.position
        })
    return JsonResponse({}, status=400)

@require_GET
def check_ppe_availability(request):
    ppe_name = request.GET.get('ppe_name')

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        quantity = ppe.quantity

        can_assign = quantity > 0
        message = '' if can_assign else 'No hay suficiente cantidad disponible.'

        response = {
            'can_assign': can_assign,
            'available': quantity,
            'message': message
        }
    except Ppe.DoesNotExist:
        response = {
            'can_assign': False,
            'available': 0,
            'message': 'EPP no encontrado.'
        }

    return JsonResponse(response)

@require_http_methods(["GET"])
def check_ppe_duration(request):
    ppe_name = request.GET.get('ppe_name')

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        return JsonResponse({
            'success': True,
            'duration': ppe.duration
        })
    except Ppe.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'EPP no encontrado.'
        }, status=404) 

@require_GET
def check_ppe_assignment(request):
    ppe_name = request.GET.get('ppe_name')
    worker_dni = request.GET.get('worker_dni')

    if not ppe_name or not worker_dni:
        return JsonResponse({'error': 'Se requieren nombre de EPP y DNI del trabajador'}, status=400)

    try:
        ppe = Ppe.objects.get(name=ppe_name)
    except Ppe.DoesNotExist:
        return JsonResponse({'error': 'EPP no encontrado'}, status=404)

    # Buscar préstamos activos para este EPP y trabajador
    active_loan = PpeLoan.objects.filter(
        ppe=ppe,
        workerDni=worker_dni,
        expirationDate__gt=timezone.now().date(),
        confirmed=True
    ).first()

    is_assigned = active_loan is not None

    return JsonResponse({
        'is_assigned': is_assigned,
        'loan_id': active_loan.idPpeLoan if active_loan else None
    })
    
@csrf_exempt
def process_ppe_loan(loan):
    ppe_name = loan.get('name')
    quantity = int(loan.get('quantity', 0))
    
    worker_data = loan.get('worker', {})
    worker_name = worker_data.get('name')
    worker_dni = worker_data.get('dni')
    worker_position = worker_data.get('position')
    
    loan_date_str = loan.get('loanDate')
    is_renewal = loan.get('isRenewal', False)
    is_exception = loan.get('isAssigned', False)
    
    if not ppe_name:
        return {'success': False, 'error': 'Falta el nombre del EPP'}
    
    if not loan_date_str:
        return {'success': False, 'error': 'Falta la fecha de préstamo'}
    
    try:
        loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'error': 'Formato de fecha inválido'}
    
    try:
        ppe = Ppe.objects.get(name=ppe_name)
        worker = Worker.objects.get(dni=worker_dni)
    except Ppe.DoesNotExist:
        return {'success': False, 'error': f'EPP {ppe_name} no encontrado'}
    except Worker.DoesNotExist:
        return {'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'}

    # Verificar duración y asignación activa
    duration_check = check_ppe_loan_duration(ppe, worker, loan_date)
    if not duration_check['can_assign'] and not (is_renewal or is_exception):
        return {'success': False, 'error': duration_check['message']}

    # Verificar cantidad disponible
    if ppe.quantity < quantity:  # Cambiado de ppe.quantity a ppe.stock
        return {'success': False, 'error': f'Cantidad insuficiente disponible para {ppe_name}'}

    # Procesar el préstamo
    active_loan = PpeLoan.objects.filter(
        ppe=ppe,
        worker=worker,
        loanDate__lte=loan_date,
        expirationDate__gte=loan_date
    ).first()

    if active_loan:
        if is_renewal or is_exception:
            ppe_duration = ppe.duration
            new_expiration_date = loan_date + timedelta(days=ppe_duration)
            active_loan.expirationDate = new_expiration_date
            active_loan.save()
            return {'success': True, 'message': f'Préstamo actualizado para {ppe_name} asignado a {worker.name}'}
        else:
            return {'success': False, 'error': f'El EPP {ppe_name} ya está prestado al trabajador {worker.name}'}
    else:
        new_loan = PpeLoan(
            worker=worker,
            workerPosition=worker_position,
            workerDni=worker_dni,
            loanDate=loan_date,
            loanAmount=quantity,
            ppe=ppe,
            confirmed=True
        )
        new_loan.save()
        ppe.quantity -= quantity  # Actualizar stock en lugar de quantity
        ppe.save()
        return {'success': True, 'message': f'Nuevo préstamo creado para {ppe_name} asignado a {worker.name}'}

def check_ppe_loan_duration(ppe, worker, loan_date):
    last_loan = PpeLoan.objects.filter(ppe=ppe, worker=worker).order_by('-loanDate').first()
    if last_loan:
        days_since_last_loan = (loan_date - last_loan.loanDate).days
        if days_since_last_loan < ppe.duration:
            return {
                'can_assign': False,
                'message': f'No se puede asignar el EPP. Deben pasar al menos {ppe.duration} días desde el último préstamo.'
            }
    return {'can_assign': True, 'message': 'Se puede asignar el EPP.'}

import traceback

@csrf_exempt
def confirm_ppe_loan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Datos recibidos:", json.dumps(data, indent=2))  # Depuración mejorada
            ppe_loans = data.get('ppe_loans', [])
            responses = []

            for loan in ppe_loans:
                try:
                    response = process_ppe_loan(loan)
                    responses.append(response)
                except Exception as e:
                    print(f"Error procesando préstamo: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
                    responses.append({'success': False, 'error': str(e)})

            if any(not r['success'] for r in responses):
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            return JsonResponse({'success': True, 'messages': responses})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)
        except Exception as e:
            print(f"Error general: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def delete_ppe_loan(request, id):
    ppe_loans = get_object_or_404(PpeLoan, idPpeLoan=id)
    
    if request.method == 'POST':
        ppe_loans.delete()
        return redirect('ppe_loan_list')
    else:
        return render(request, 'delete_ppe_loan.html', {'ppe_loans': ppe_loans})
    
@login_required
def modify_ppe_loan(request, id):
    ppe_loans = get_object_or_404(PpeLoan, idPpeLoan=id)

    if request.method == 'POST':
        form = PpeLoanForm(request.POST, request.FILES, instance=ppe_loans)
        if form.is_valid():
            form.instance.status = True
            form.save()
            return redirect('ppe_loan_list')
    else:
        return render(request, 'modify_ppe_loan.html', {'form': form})
    
#historial

def history(request):
    history_records = History.objects.all().order_by('-timestamp')
    return render(request, 'history.html', {'history_records': history_records})
    
#REGISTER
def register_admin(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('login')
        else:
            print(form.errors)
    else:
        form = AdminSignUpForm()
    return render(request, 'register_admin.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def user_list(request):
    query = request.GET.get('q', '')
    if query:
        admin = User.objects.filter(admin__name_icontains=query)
    else:
        admin = User.objects.all()
    print(f"Número de usuarios: {admin.count()}")
    return render(request, 'table_user.html', {'admin': admin, 'query': query})

def exit(request):
    logout(request)
    return redirect('home')