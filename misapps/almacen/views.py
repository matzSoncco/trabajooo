from django.shortcuts import render, redirect
from decimal import Decimal
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect
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
import traceback
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
from .models.EquipmentStockUpdate import EquipmentStockUpdate
from .models.ToolStockUpdate import ToolStockUpdate
from .models.ToolLoan import ToolLoan
from .models.Equipment import Equipment
from .models.EquipmentLoan import EquipmentLoan
from .models.Worker import Worker
from .models.Material import Material
from .models.MaterialLoan import MaterialLoan
from .models.MaterialStockUpdate import MaterialStockUpdate
from .models.Tool import Tool
from .models.History import History
from .models.Unit import Unit
from .models.PpeStockUpdate import PpeStockUpdate
from .forms import AdminSignUpForm, PpeForm, MaterialForm, WorkerForm, EquipmentForm, ToolForm, PpeLoanForm, Ppe, CreatePpeForm, CreateMaterialForm, CreateEquipmentForm, CreateToolForm, PpeStockUpdateForm, ToolLoanForm, EquipmentLoanForm, MaterialLoanForm

logger = logging.getLogger(__name__)

# Create your views here.
def home(request):
    return render(request, 'home.html')

#DURACIÓN
@login_required
def set_duration(request):
    form = PpeForm()
    query = request.GET.get('q', '')
    if query:
        epp = Ppe.objects.filter(name__icontains=query)
    else:
        epp = Ppe.objects.all()

    context = {
        'form': form,
        'epp': epp,
        'query': query
    }
    return render(request, 'show_duration_table.html', context)

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

@csrf_exempt
@login_required
def update_ppe_duration(request):
    if request.method == 'POST':
        try:
            # Obtener el ID y la nueva duración del PPE
            ppe_id = request.POST.get('ppe_id')
            new_duration = request.POST.get('duration')
            
            # Usar el campo correcto para obtener el PPE
            ppe = Ppe.objects.get(idPpe=ppe_id)
            
            # Actualizar la duración del PPE
            ppe.duration = new_duration
            ppe.save()
            
            # Registrar la acción en el historial
            History.objects.create(
                content_type=ContentType.objects.get_for_model(ppe),
                object_name=ppe.name,
                action='Actualizar Duración',
                user=request.user,
                timestamp=timezone.now()
            )
            
            return JsonResponse({'status': 'success'})
        except Ppe.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'PPE no encontrado'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'})
#PPE
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
                # Validación de campos vacíos o cero
                if not item.get('name'):
                    return JsonResponse({'status': 'error', 'message': 'Nombre del EPP es obligatorio.'})
                if int(item.get('quantity', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Cantidad debe ser mayor que 0.'})
                if Decimal(item.get('unitCost', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Costo unitario debe ser mayor que 0.'})
                if int(item.get('stock', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Stock ideal debe ser mayor que 0.'})

                try:
                    ppe = Ppe.objects.get(name=item['name'])
                except Ppe.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'EPP con nombre {item["name"]} no existe.'})

                quantity = int(item['quantity'])
                new_unit_cost = Decimal(item['unitCost'])
                stock = int(item['stock'])
                guideNumber = item['guideNumber']

                # Calcular el costo promedio
                total_updates = PpeStockUpdate.objects.filter(ppe=ppe).count()

                if total_updates == 0:
                    # Primera vez que se ingresa este EPP
                    average_cost = new_unit_cost
                else:
                    # Calcular el promedio con el nuevo costo
                    total_cost = (ppe.unitCost * Decimal(ppe.quantity)) + (new_unit_cost * quantity)
                    total_quantity = ppe.quantity + quantity
                    average_cost = total_cost / total_quantity

                # Actualizar el EPP
                ppe.quantity += quantity
                ppe.unitCost = average_cost
                ppe.stock = stock
                ppe.guideNumber = guideNumber
                ppe.save()

                # Crear registros de historial y actualización de stock
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(ppe),
                    object_name=ppe.name,
                    action='Ingreso Stock',
                    user=request.user,
                    timestamp=timezone.now()
                )

                PpeStockUpdate.objects.create(
                    ppe=ppe,
                    quantity=quantity,
                    unitCost=new_unit_cost,
                    date=item['creationDate'],                   
                )

            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al decodificar JSON.'})
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

def ppe_total_add(request):
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
            form = PpeForm(request.POST, request.FILES, instance=ppe)
        else:
            form = PpeForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Imprimir los datos del formulario para depuración
            print("Datos del formulario:")
            for field in form.cleaned_data:
                print(f"{field}: {form.cleaned_data[field]}")
            
            ppe = form.save(commit=False)
            # Asegúrate de que guideNumber se establezca explícitamente
            ppe.guideNumber = form.cleaned_data['guideNumber']
            ppe.save()
            messages.success(request, 'EPP guardado exitosamente.')
            return redirect('ppe_total')
        else:
            print("Errores del formulario:", form.errors)
    else:
        form = PpeForm()
    return render(request, 'ppe_total_add.html', {'ppes': ppes, 'form': form})

@login_required
def create_ppe(request):
    if request.method == 'POST':
        form = CreatePpeForm(request.POST, request.FILES)

        new_unit_name = request.POST.get('new_unit')
        if new_unit_name:
            # Crear o recuperar la unidad nueva
            unit, created = Unit.objects.get_or_create(name=new_unit_name)
            post_data = request.POST.copy()
            post_data['unit'] = unit.id
            form = CreatePpeForm(post_data, request.FILES)  # Crear un nuevo formulario con la nueva unidad

        # Validar si ya existe un EPP con el mismo nombre
        existing_ppe = Ppe.objects.filter(name=form.data.get('name')).exists()
        if existing_ppe:
            form.add_error('name', 'Ya existe un EPP con este nombre.')

        if form.is_valid():
            ppe = form.save(commit=False)
            ppe.save()

            # Registrar la acción en el historial
            History.objects.create(
                content_type=ContentType.objects.get_for_model(ppe),
                object_name=ppe.name,
                action='Creado',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'EPP creado exitosamente.')
            return redirect('create_ppe')
        else:
            # Manejo de errores y mensajes
            error_added = False
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'name' and 'Ya existe un EPP con este nombre.' in error:
                        messages.error(request, 'Ya existe un EPP con este nombre.')
                        error_added = True
                    else:
                        messages.error(request, f"Error en el campo '{form[field].label}': {error}")
                        error_added = True

            if not error_added:
                messages.error(request, 'Error al crear el EPP. Verifique los campos e intente nuevamente.')
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
            History.objects.create(
                content_type=ContentType.objects.get_for_model(unit),
                object_name=unit.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )
            if created:
                return JsonResponse({'success': True, 'unit': unit.name})
            else:
                return JsonResponse({'success': False, 'message': 'La unidad ya existe.'})
        return JsonResponse({'success': False, 'message': 'Nombre de la unidad no proporcionado.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Error al procesar la solicitud.'})

@login_required
def add_ppe(request):
    query = request.GET.get('q', '')  # Obtener el parámetro de búsqueda
    if query:
        epp = Ppe.objects.filter(name__icontains=query)
    else:
        epp = Ppe.objects.all()
    
    if request.method == 'POST':
        form = PpeForm(request.POST)
        if form.is_valid():
            guideNumber = form.cleaned_data['guideNumber']
            creationDate = form.cleaned_data['creationDate']
            name = form.cleaned_data['name']
            new_unit_cost = Decimal(form.cleaned_data['unitCost'])
            quantity = int(form.cleaned_data['quantity'])
            stock = int(form.cleaned_data['stock'])
            
            # Validaciones adicionales
            if quantity <= 0:
                form.add_error('quantity', 'La cantidad debe ser un número positivo mayor a 0.')
            if stock <= 0:
                form.add_error('stock', 'El stock debe ser un número positivo mayor a 0.')
            if not Ppe.objects.filter(name=name).exists():
                form.add_error('name', 'El EPP debe coincidir con un EPP existente.')
            
            if form.errors:
                messages.error(request, 'Error al añadir EPP. Verifique los campos e intente nuevamente.')
            else:
                ppe, created = Ppe.objects.get_or_create(name=name)
                
                total_updates = PpeStockUpdate.objects.filter(ppe=ppe).count()
                
                if total_updates == 0 or created:
                    # Primera vez que se ingresa este EPP
                    average_cost = new_unit_cost
                else:
                    # Calcular el promedio con el nuevo costo
                    total_cost = (ppe.unitCost * Decimal(ppe.quantity)) + (new_unit_cost * quantity)
                    total_quantity = ppe.quantity + quantity
                    average_cost = total_cost / total_quantity

                ppe.quantity += quantity
                ppe.unitCost = average_cost
                ppe.stock = stock
                ppe.guideNumber = guideNumber
                ppe.save()
                
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(ppe),
                    object_name=ppe.name,
                    action='Ingresar Stock',
                    user=request.user,
                    timestamp=timezone.now()
                )
                
                PpeStockUpdate.objects.create(
                    ppe=ppe,
                    quantity=quantity,
                    unitCost=new_unit_cost,
                    date=creationDate,
                )
                
                messages.success(request, 'Se añadió EPP correctamente.')
                return redirect('add_ppe')

        else:
            messages.error(request, 'Error al añadir EPP. Verifique los campos e intente nuevamente.')
            print("Formulario no válido")
            print(form.errors)

    else:
        form = PpeForm()
    
    context = {
        'form': form,
        'epp': epp,
        'query': query
    }
    return render(request, 'add_ppe.html', context)

@login_required
def delete_ppe(request, ppe_id):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            if data.get('confirm') == 'yes':
                ppe = get_object_or_404(Ppe, idPpe=ppe_id)
                ppe_name = ppe.name
                ppe.delete()
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(ppe),
                    object_name=ppe_name,
                    action='Deleted',
                    user=request.user,
                    timestamp=timezone.now()
                )
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'error'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)

@login_required
def modify_ppe(request, ppe_id):
    ppe = get_object_or_404(Ppe, idPpe=ppe_id)

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
                action='Modificar',
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
def modify_ppe_add(request, name):
    ppe = get_object_or_404(Ppe, name=name)

    if request.method == 'POST':
        form = CreatePpeForm(request.POST, request.FILES, instance=ppe)

        new_unit_name = request.POST.get('new_unit')
        if new_unit_name:
            unit, created = Unit.objects.get_or_create(name=new_unit_name)
            post_data = request.POST.copy()
            post_data['unit'] = unit.id
            form = PpeForm(post_data, request.FILES, instance=ppe)
        
        if form.is_valid():
            ppe = form.save(commit=False)
            ppe.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(ppe),
                object_name=ppe.name, 
                action='Modificar',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'EPP modificado exitosamente.')
            return redirect('ppe_total')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = PpeForm(instance=ppe)

    return render(request, 'modify_ppe_add.html', {'form': form, 'ppe': ppe})

@login_required 
def total_ppe_stock(request):
    total_stock = Ppe.objects.aggregate(Sum('stock'))['stock__sum'] or 0
    return JsonResponse({'total_stock': total_stock})

#EQUIMENT
@login_required
def add_equipment(request):
    query = request.GET.get('q', '')
    if query:
        equipment = Equipment.objects.filter(name__icontains=query)
    else:
        equipment = Equipment.objects.all()

    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            guideNumber = form.cleaned_data['guideNumber']
            creationDate = form.cleaned_data['creationDate']
            name = form.cleaned_data['name']
            new_unit_cost = Decimal(form.cleaned_data['unitCost'])
            quantity = int(form.cleaned_data['quantity'])
            stock = int(form.cleaned_data['stock'])
            
            # Obtener o crear el objeto Ppe
            equipment, created = Equipment.objects.get_or_create(name=name)
            
            total_updates = EquipmentStockUpdate.objects.filter(equipment=equipment).count()
                
            if total_updates == 0 or created:
                # Primera vez que se ingresa este EPP
                average_cost = new_unit_cost
            else:
                # Calcular el promedio con el nuevo costo
                total_cost = (equipment.unitCost * Decimal(equipment.quantity)) + (new_unit_cost * quantity)
                total_quantity = equipment.quantity + quantity
                average_cost = total_cost / total_quantity

            equipment.quantity += quantity
            equipment.unitCost = average_cost
            equipment.stock = stock
            equipment.guideNumber = guideNumber
            equipment.save()
            
            History.objects.create(
                content_type=ContentType.objects.get_for_model(equipment),
                object_name=equipment.name,
                action='Ingresar Stock',
                user=request.user,
                timestamp=timezone.now()
            )
            # Crear el registro de actualización de stock
            EquipmentStockUpdate.objects.create(
                equipment=equipment,
                quantity=quantity,
                unitCost=new_unit_cost,
                date=creationDate
            )
            messages.success(request, 'Se añadió equipos correctamente.')
            return redirect('add_equipment')
    else:
        form = EquipmentForm()
    
    context = {
        'form': form,
        'equipment': equipment,
        'query': query
    }
    return render(request, 'add_equipment.html', context)

def get_equipment_data(request):
    equipment_id = request.GET.get('id')
    equipment = get_object_or_404(Equipment, idEquipment=equipment_id)
    data = {
        'guideNumber': equipment.guideNumber,
        'creationDate': equipment.creationDate,
        'name': equipment.name,
        'unitCost': equipment.unitCost,
        'quantity': equipment.quantity,
        'stock': equipment.stock
    }
    return JsonResponse(data)

@csrf_exempt
def save_all_equipment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            for item in data:
                # Validación de campos vacíos o cero
                if not item.get('name'):
                    return JsonResponse({'status': 'error', 'message': 'Nombre del equipo es obligatorio.'})
                if int(item.get('quantity', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Cantidad debe ser mayor que 0.'})
                if Decimal(item.get('unitCost', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Costo unitario debe ser mayor que 0.'})
                if int(item.get('stock', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Stock ideal debe ser mayor que 0.'})
                
                try:
                    equipment = Equipment.objects.get(name=item['name'])
                except Equipment.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Equipo con nombre {item["name"]} no existe.'})
                
                quantity = int(item['quantity'])
                new_unit_cost = Decimal(item['unitCost'])
                stock = int(item['stock'])
                guideNumber = item['guideNumber']

                # Calcular el costo promedio
                total_updates = EquipmentStockUpdate.objects.filter(equipment=equipment).count()

                if total_updates == 0:
                    # Primera vez que se ingresa este EPP
                    average_cost = new_unit_cost
                else:
                    # Calcular el promedio con el nuevo costo
                    total_cost = (equipment.unitCost * Decimal(equipment.quantity)) + (new_unit_cost * quantity)
                    total_quantity = equipment.quantity + quantity
                    average_cost = total_cost / total_quantity

                # Actualización del costo total y cantidad
                equipment.quantity += quantity
                equipment.unitCost = average_cost
                equipment.stock = stock
                equipment.guideNumber = guideNumber
                equipment.save()
                
                # Crear registros de historial y actualización de stock
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(equipment),
                    object_name=equipment.name,
                    action='Add Stock',
                    user=request.user,
                    timestamp=timezone.now()
                )
                EquipmentStockUpdate.objects.create(
                    equipment=equipment,
                    quantity=quantity,
                    unitCost=new_unit_cost,
                    date=item['creationDate'], 
                )
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al decodificar JSON.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'invalid method'})

def equipment_total_add(request):
    equipment = Equipment.objects.all()  
    
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
            form = EquipmentForm(request.POST, request.FILES, instance=equipment)
            if form.is_valid():
                form.save()
                messages.success(request, 'Equipos actualizado exitosamente.')
                return redirect('equipment_total')
    
    form = EquipmentForm()  # Inicializa el formulario para crear o editar
    return render(request, 'equipment_total_add.html', {'equipment': equipment, 'form': form})

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

        # Validar si ya existe un equipo con el mismo nombre
        existing_equipment = Equipment.objects.filter(name=form.data.get('name')).exists()
        if existing_equipment:
            form.add_error('name', 'Ya existe un equipo con este nombre.')

        if form.is_valid():
            equipment = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(equipment),
                object_name=equipment.name,
                action='Creado',
                user=request.user,
                timestamp=timezone.now()
            )
            messages.success(request, 'Equipo creado exitosamente.')
            return redirect('create_equipment')
        else:
            # Verifica si ya existe un error específico antes de agregar el mensaje general
            error_added = False
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'name' and 'Ya existe un equipo con este nombre.' in error:
                        messages.error(request, 'Ya existe un equipo con este nombre.')
                        error_added = True
                    else:
                        messages.error(request, f"Error en el campo '{form[field].label}': {error}")
                        error_added = True
                        
            # Si no hay errores específicos, agregar mensaje general
            if not error_added:
                messages.error(request, 'Error al crear el Equipo. Verifique los campos e intente nuevamente.')
    else:
        form = CreateEquipmentForm()

    return render(request, 'create_equipment.html', {'form': form})

@login_required
def delete_equipment(request, equipment_id):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            if data.get('confirm') == 'yes':
                equipment = get_object_or_404(Equipment, idMaterial=equipment_id)
                equipment_name = equipment.name
                equipment.delete()
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(equipment),
                    object_name=equipment_name,
                    action='Eliminar',
                    user=request.user,
                    timestamp=timezone.now()
                )
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'error'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)

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
                action='Modificar',
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
def get_material_data(request):
    material_id = request.GET.get('id')
    material = get_object_or_404(Material, idMaterial=material_id)
    data = {
        'guideNumber': material.guideNumber,
        'creationDate': material.creationDate,
        'name': material.name,
        'unitCost': material.unitCost,
        'quantity': material.quantity,
        'stock': material.stock
    }
    return JsonResponse(data)

@csrf_exempt
def save_all_material(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            for item in data:
                # Validaciones
                if not item.get('name'):
                    return JsonResponse({'status': 'error', 'message': 'Nombre del material es obligatorio.'})
                if int(item.get('quantity', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Cantidad debe ser mayor que 0.'})
                if Decimal(item.get('unitCost', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Costo unitario debe ser mayor que 0.'})
                if int(item.get('stock', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Stock ideal debe ser mayor que 0.'})
                if int(item.get('guideNumber', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Número guia no puede ser 0.'})
                
                try:
                    material = Material.objects.get(name=item['name'])
                except Material.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Material con nombre {item["name"]} no existe.'})
                
                quantity = int(item['quantity'])
                new_unit_cost = Decimal(item['unitCost'])
                stock = int(item['stock'])
                creationDate = item.get('creationDate')
                guideNumber = item['guideNumber']

                # Calcular el costo promedio
                total_updates = MaterialStockUpdate.objects.filter(material=material).count()

                if total_updates == 0:
                    # Primera vez que se ingresa este EPP
                    average_cost = new_unit_cost
                else:
                    # Calcular el promedio con el nuevo costo
                    total_cost = (material.unitCost * Decimal(material.quantity)) + (new_unit_cost * quantity)
                    total_quantity = material.quantity + quantity
                    average_cost = total_cost / total_quantity

                # Actualizar el EPP
                material.quantity += quantity
                material.unitCost = average_cost
                material.stock = stock
                material.guideNumber = guideNumber
                material.save()
                
                # Crear registros de historial y actualización de stock
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(material),
                    object_name=material.name,
                    action='Ingreso Stock',
                    user=request.user,
                    timestamp=timezone.now()
                )

                MaterialStockUpdate.objects.create(
                    material=material,
                    quantity=quantity,
                    unitCost=new_unit_cost,
                    date=creationDate
                )
            
            return JsonResponse({'status': 'success'})
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al decodificar JSON.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'invalid method'})

def material_total_add(request):
    material = Material.objects.all()  
    
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
            form = MaterialForm(request.POST, request.FILES, instance=material)
            if form.is_valid():
                form.save()
                messages.success(request, 'Material actualizado exitosamente.')
                return redirect('material_total')
    
    form = MaterialForm()  # Inicializa el formulario para crear o editar
    return render(request, 'material_total_add.html', {'material': material, 'form': form})

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

        # Validar si ya existe un material con el mismo nombre
        existing_material = Material.objects.filter(name=form.data.get('name')).exists()
        if existing_material:
            form.add_error('name', 'Ya existe un material con este nombre.')

        if form.is_valid():
            material = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(material),
                object_name=material.name,
                action='Creado',
                user=request.user,
                timestamp=timezone.now()
            )
            print(f"Material creado: {material.idMaterial}")
            print(f"Datos del POST: {request.POST}")
            messages.success(request, 'Material creado exitosamente.')
            return redirect('create_material')
        else:
            # Verifica si el error específico es por nombre duplicado
            if form.errors.get('name'):
                messages.error(request, 'Ya existe un material con este nombre. Por favor, elija un nombre diferente.')
            else:
                messages.error(request, 'Error al crear el material. Verifique los campos e intente nuevamente.')
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
    query = request.GET.get('q', '')
    if query:
        material = Material.objects.filter(name__icontains=query)
    else:
        material = Material.objects.all()

    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            # Obtener datos del formulario y convertirlos a los tipos correctos
            guideNumber = form.cleaned_data['guideNumber']
            creationDate = form.cleaned_data['creationDate']
            name = form.cleaned_data['name']
            new_unit_cost = Decimal(form.cleaned_data['unitCost'])
            quantity = int(form.cleaned_data['quantity'])
            stock = int(form.cleaned_data['stock'])
            
            # Obtener o crear el objeto Ppe
            material, created = Material.objects.get_or_create(name=name)
            
            total_updates = MaterialStockUpdate.objects.filter(material=material).count()
                
            if total_updates == 0 or created:
                # Primera vez que se ingresa este EPP
                average_cost = new_unit_cost
            else:
                # Calcular el promedio con el nuevo costo
                total_cost = (material.unitCost * Decimal(material.quantity)) + (new_unit_cost * quantity)
                total_quantity = material.quantity + quantity
                average_cost = total_cost / total_quantity

            material.quantity += quantity
            material.unitCost = average_cost
            material.stock = stock
            material.guideNumber = guideNumber
            material.save()
            
            History.objects.create(
                content_type=ContentType.objects.get_for_model(material),
                object_name=material.name,
                action='Add Stock',
                user=request.user,
                timestamp=timezone.now()
            )

            # Crear el registro de actualización de stock
            PpeStockUpdate.objects.create(
                material=material,
                quantity=quantity,
                unitCost=new_unit_cost,
                date=creationDate
            )
            messages.success(request, 'Se añadió material correctamente.')
            return redirect('add_material')
    else:
        form = MaterialForm()

    context = {
        'form': form,
        'material': material,
        'query': query
    }
    return render(request, 'add_material.html', context)

@login_required
def delete_material(request, material_id):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            if data.get('confirm') == 'yes':
                material = get_object_or_404(Material, idMaterial=material_id)
                material_name = material.name
                material.delete()
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(material),
                    object_name=material_name,
                    action='Eliminar',
                    user=request.user,
                    timestamp=timezone.now()
                )
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'error'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)

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
                action='Modificar',
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
def get_tool_data(request):
    tool_id = request.GET.get('id')
    tool = get_object_or_404(Tool, idTool=tool_id)
    data = {
        'guideNumber': tool.guideNumber,
        'creationDate': tool.creationDate,
        'name': tool.name,
        'unitCost': tool.unitCost,
        'quantity': tool.quantity,
        'stock': tool.stock,
        'level': tool.level,
    }
    return JsonResponse(data)
@login_required
def add_tool(request):
    query = request.GET.get('q', '')
    if query:
        tool = Tool.objects.filter(name__icontains=query)
    else:
        tool = Tool.objects.all()

    if request.method == 'POST':
        form = ToolForm(request.POST, request.FILES)
        if form.is_valid():
            guideNumber = form.cleaned_data['guideNumber']
            creationDate = form.cleaned_data.get('creationDate')
            name = form.cleaned_data['name']
            new_unit_cost = Decimal(form.cleaned_data['unitCost'])
            quantity = int(form.cleaned_data['quantity'])
            stock = int(form.cleaned_data['stock'])
            level = int(form.cleaned_data['level'])
            
            tool, created = Tool.objects.get_or_create(name=name)
            
            total_updates = PpeStockUpdate.objects.filter(tool=tool).count()
                
            if total_updates == 0 or created:
                # Primera vez que se ingresa este EPP
                average_cost = new_unit_cost
            else:
                # Calcular el promedio con el nuevo costo
                total_cost = (tool.unitCost * Decimal(tool.quantity)) + (new_unit_cost * quantity)
                total_quantity = tool.quantity + quantity
                average_cost = total_cost / total_quantity

            tool.quantity += quantity
            tool.unitCost = average_cost
            tool.stock = stock
            tool.guideNumber = guideNumber
            tool.level = level
            tool.save()
            
            History.objects.create(
                content_type=ContentType.objects.get_for_model(tool),
                object_name=tool.name,
                action='Ingresar Stock',
                user=request.user,
                timestamp=timezone.now()
            )

            # Create the stock update record
            ToolStockUpdate.objects.create(
                tool=tool,
                quantity=quantity,
                unitCost=new_unit_cost,
                date=creationDate
            )
            messages.success(request, 'Se añadió herramientas correctamente.')
            return redirect('add_tool')
    else:
        form = ToolForm()

    context = {
        'form': form,
        'tool': tool,
        'query': query
    }
    return render(request, 'add_tool.html', context)


@csrf_exempt
def save_all_tools(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            for item in data:
                # Validación de campos vacíos o cero
                if not item.get('name'):
                    return JsonResponse({'status': 'error', 'message': 'Nombre de la herramienta es obligatorio.'})
                if int(item.get('quantity', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Cantidad debe ser mayor que 0.'})
                if Decimal(item.get('unitCost', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Costo unitario debe ser mayor que 0.'})
                if int(item.get('stock', 0)) <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Stock ideal debe ser mayor que 0.'})
                
                try:
                    tool = Tool.objects.get(name=item['name'])
                except Tool.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Herramienta con nombre {item["name"]} no existe.'})

                quantity = int(item['quantity'])
                new_unit_cost = Decimal(item['unitCost'])
                stock = int(item['stock'])
                creationDate = item.get('creationDate')
                guideNumber = item['guideNumber']

                # Calcular el costo promedio
                total_updates = ToolStockUpdate.objects.filter(tool=tool).count()

                if total_updates == 0:
                    # Primera vez que se ingresa este EPP
                    average_cost = new_unit_cost
                else:
                    # Calcular el promedio con el nuevo costo
                    total_cost = (tool.unitCost * Decimal(tool.quantity)) + (new_unit_cost * quantity)
                    total_quantity = tool.quantity + quantity
                    average_cost = total_cost / total_quantity

                # Actualizar el EPP
                tool.quantity += quantity
                tool.unitCost = average_cost
                tool.stock = stock
                tool.guideNumber = guideNumber
                tool.save()

                # Crear registros de historial y actualización de stock
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(tool),
                    object_name=tool.name,
                    action='Ingreso Stock',
                    user=request.user,
                    timestamp=timezone.now()
                )

                ToolStockUpdate.objects.create(
                    tool=tool,
                    quantity=quantity,
                    unitCost=new_unit_cost,
                    date=creationDate
                )

            return JsonResponse({'status': 'success'})
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Error al decodificar JSON.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'invalid method'})

def tool_total_add(request):
    tools = Tool.objects.all()  
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            tool_id = request.POST.get('delete')
            tool = get_object_or_404(Tool, id=tool_id)
            tool.delete()
            messages.success(request, 'Herramienta eliminada exitosamente.')
            return redirect('tool_total')

        if 'edit' in request.POST:
            tool_id = request.POST.get('edit')
            tool = get_object_or_404(Tool, id=tool_id)
            form = ToolForm(request.POST, request.FILES, instance=tool)
            if form.is_valid():
                form.save()
                messages.success(request, 'Herramienta actualizado exitosamente.')
                return redirect('tool_total')
    
    form = ToolForm()  # Inicializa el formulario para crear o editar
    return render(request, 'tool_total_add.html', {'tools': tools, 'form': form})

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

        # Validar si ya existe una herramienta con el mismo nombre
        existing_tool = Tool.objects.filter(name=form.data.get('name')).exists()
        if existing_tool:
            form.add_error('name', 'Ya existe una herramienta con este nombre.')

        if form.is_valid():
            tool = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(tool),
                object_name=tool.name,
                action='Creado',
                user=request.user,
                timestamp=timezone.now()
            )
            messages.success(request, 'Herramienta guardada exitosamente.')
            return redirect('create_tool')
        else:
            # Verifica si el error específico es por nombre duplicado
            if form.errors.get('name'):
                messages.error(request, 'Ya existe una herramienta con este nombre. Por favor, elija un nombre diferente.')
            else:
                messages.error(request, 'Error al guardar la herramienta. Verifique los campos e intente nuevamente.')
            print("Form is not valid")
            print(form.errors)
    else:
        form = CreateToolForm()
    return render(request, 'create_tool.html', {'form': form})

@login_required
def delete_tool(request, tool_id):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            if data.get('confirm') == 'yes':
                tool = get_object_or_404(Tool, idMaterial=tool_id)
                tool_name = tool.name
                tool.delete()
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(tool),
                    object_name=tool_name,
                    action='Eliminar',
                    user=request.user,
                    timestamp=timezone.now()
                )
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'error'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)

@login_required
def modify_tool(request, tool_name):
    print(f"Received tool_name: {tool_name}")
    tool = get_object_or_404(Tool, name=tool_name)
    if request.method == 'POST':
        form = CreateToolForm(request.POST, request.FILES, instance=tool)
        
        if form.is_valid():
            tool = form.save(commit=False)
            tool.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(tool),
                object_name=tool.name, 
                action='Modificar',
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

@login_required
def return_view(request):
    # Obtener todos los préstamos de herramientas y equipos
    tool_loans = ToolLoan.objects.all()
    equipment_loans = EquipmentLoan.objects.all()

    # Manejo de la búsqueda
    work_order = request.GET.get('work_order')
    worker_dni = request.GET.get('worker_dni')

    if work_order:
        tool_loans = tool_loans.filter(workOrder=work_order)
        equipment_loans = equipment_loans.filter(workOrder=work_order)
    elif worker_dni:
        tool_loans = tool_loans.filter(workerDni=worker_dni)
        equipment_loans = equipment_loans.filter(workerDni=worker_dni)
    elif 'view_debtors' in request.GET:
        tool_loans = tool_loans.filter(loanStatus=False)
        equipment_loans = equipment_loans.filter(loanStatus=False)

    # Manejo del POST para actualizar loanStatus
    if request.method == 'POST':
        for loan in tool_loans:
            checkbox_name = f'returned_tool_{loan.idToolLoan}'
            loan.loanStatus = checkbox_name in request.POST
            loan.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(loan),
                object_name=loan.tool.name,
                action='Return',
                user=request.user,
                timestamp=timezone.now()
            )

        for loan in equipment_loans:
            checkbox_name = f'returned_equipment_{loan.idEquipmentLoan}'
            loan.loanStatus = checkbox_name in request.POST
            loan.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(loan),
                object_name=loan.equipment.name,
                action='Return',
                user=request.user,
                timestamp=timezone.now()
            )
        
        return HttpResponseRedirect(request.path_info)

    return render(request, 'return.html', {
        'tool_loans': tool_loans,
        'equipment_loans': equipment_loans,
        'show_debtors': 'view_debtors' in request.GET,
    })
@login_required
def return_tool_view(request):
    tool_loans = ToolLoan.objects.all()

    # Manejo de la búsqueda
    work_order = request.GET.get('work_order')
    worker_dni = request.GET.get('worker_dni')

    if work_order:
        tool_loans = tool_loans.filter(workOrder=work_order)
    elif worker_dni:
        tool_loans = tool_loans.filter(workerDni=worker_dni)
    elif 'view_debtors' in request.GET:
        tool_loans = tool_loans.filter(loanStatus=False)

    # Manejo del POST para actualizar loanStatus
    if request.method == 'POST':
        for loan in tool_loans:
            checkbox_name = f'returned_tool_{loan.idToolLoan}'
            loan.loanStatus = checkbox_name in request.POST
            loan.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(loan),
                object_name=loan.tool.name,
                action='Return',
                user=request.user,
                timestamp=timezone.now()
            )
        return HttpResponseRedirect(request.path_info)

    return render(request, 'return_tool.html', {
        'tool_loans': tool_loans,
        'show_debtors': 'view_debtors' in request.GET,
    })

@login_required
def return_equipment_view(request):
    equipment_loans = EquipmentLoan.objects.all()

    # Manejo de la búsqueda
    work_order = request.GET.get('work_order')
    worker_dni = request.GET.get('worker_dni')

    if work_order:
        equipment_loans = equipment_loans.filter(workOrder=work_order)
    elif worker_dni:
        equipment_loans = equipment_loans.filter(workerDni=worker_dni)
    elif 'view_debtors' in request.GET:
        equipment_loans = equipment_loans.filter(loanStatus=False)

    # Manejo del POST para actualizar loanStatus
    if request.method == 'POST':
        for loan in equipment_loans:
            checkbox_name = f'returned_equipment_{loan.idEquipmentLoan}'
            loan.loanStatus = checkbox_name in request.POST
            loan.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(loan),
                object_name=loan.equipment.name,
                action='Return',
                user=request.user,
                timestamp=timezone.now()
            )
        return HttpResponseRedirect(request.path_info)

    return render(request, 'return_equipment.html', {
        'equipment_loans': equipment_loans,
        'show_debtors': 'view_debtors' in request.GET,
    })

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
            dni = form.cleaned_data.get('dni')
            name = form.cleaned_data.get('name')
            surname = form.cleaned_data.get('surname')

            if Worker.objects.filter(dni=dni).exists():
                messages.error(request, 'Ya existe un trabajador con este DNI.')
                return render(request, 'create_worker.html', {'form': form})

            if Worker.objects.filter(name=name, surname=surname).exists():
                messages.error(request, 'Ya existe un trabajador con este nombre y apellido.')
                return render(request, 'create_worker.html', {'form': form})

            worker = form.save()
            History.objects.create(
                content_type=ContentType.objects.get_for_model(worker),
                object_name=worker.name,
                action='Created',
                user=request.user,
                timestamp=timezone.now()
            )
            messages.success(request, 'Trabajador creado con éxito')
            return redirect('create_worker')
        else:
            messages.error(request, 'Hubo un error al crear el trabajador. Por favor, revisa el formulario.')
            return render(request, 'create_worker.html', {'form': form})
    else:
        form = WorkerForm()
    return render(request, 'create_worker.html', {'form': form})

    
@login_required
def delete_worker(request, worker_id):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            if data.get('confirm') == 'yes':
                worker = get_object_or_404(Worker, dni=worker_id)
                worker_name = worker.name
                worker.delete()
                History.objects.create(
                    content_type=ContentType.objects.get_for_model(worker),
                    object_name=worker_name,
                    action='Eliminar',
                    user=request.user,
                    timestamp=timezone.now()
                )
                return JsonResponse({'status': 'success'}, status=200)
            return JsonResponse({'status': 'error'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)

@login_required
def modify_worker(request, name):
    worker = get_object_or_404(Worker, name=name)

    if request.method == 'POST':
        form = WorkerForm(request.POST, request.FILES, instance=worker)
        
        if form.is_valid():
            worker = form.save(commit=False)
            worker.save()

            History.objects.create(
                content_type=ContentType.objects.get_for_model(worker),
                object_name=worker.name, 
                action='Modificar',
                user=request.user,
                timestamp=timezone.now()
            )

            messages.success(request, 'Trabajador modificado exitosamente.')
            return redirect('worker_list')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = WorkerForm(instance=worker)

    return render(request, 'modify_worker.html', {'form': form, 'worker': worker})

#TOOLLOAN
@login_required
def tool_loan_list(request):
    query = request.GET.get('q', '')
    dni_query = request.GET.get('dni', '')

    if query and dni_query:
        # Filtrar por nombre y DNI
        tool_loans = ToolLoan.objects.filter(
            worker__name__icontains=query,
            worker__dni__icontains=dni_query
        )
    elif query:
        # Filtrar solo por nombre
        tool_loans = ToolLoan.objects.filter(worker__name__icontains=query)
    elif dni_query:
        # Filtrar solo por DNI
        tool_loans = ToolLoan.objects.filter(worker__dni__icontains=dni_query)
    else:
        # No hay filtros aplicados
        tool_loans = ToolLoan.objects.all()

    return render(request, 'tool_loan_list.html', {'tool_loans': tool_loans, 'query': query, 'dni_query': dni_query})

login_required
def add_tool_loan(request):
    query = request.GET.get('q', '')
    if query:
        tools = Tool.objects.filter(name__icontains=query)
    else:
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
    
    context = {
        'form': form,
        'tools': tools,
        'query': query
    }

    return render(request, 'add_tool_loan.html', context)
    
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

            # Obtenemos la Herramienta
            tool_name = cleaned_data['tool']
            try:
                tool = Tool.objects.get(name=tool_name)
            except Tool.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Herramienta no encontrada'
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
    try:
        tool_name = loan.get('name')
        worker_data = loan.get('worker', {})
        worker_name = worker_data.get('name')
        worker_position = worker_data.get('position')
        worker_dni = worker_data.get('dni')
        loan_date_str = loan.get('loanDate')
        quantity = int(loan.get('quantity'))
        is_renewal = loan.get('isRenewal', False)
        is_assigned = loan.get('isAssigned', False)

        # Verificar y convertir la fecha del préstamo
        try:
            loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return {'success': False, 'error': 'Fecha de préstamo no válida'}

        if worker_dni is None or worker_dni.strip() == "":
            return {'success': False, 'error': 'DNI del trabajador no proporcionado'}

        try:
            tool = Tool.objects.get(name=tool_name)
            worker = Worker.objects.get(dni=worker_dni)

            # Calcular la nueva fecha de expiración (si aplica)
            new_expiration_date = loan_date + timedelta(days=tool.duration)

            # Verificar si ya existe un préstamo activo
            active_loan = ToolLoan.objects.filter(
                tool=tool,
                worker=worker,
                loanDate__lte=loan_date,
                returnLoanDate__gte=loan_date
            ).first()

            if active_loan and not (is_renewal or is_assigned):
                return {
                    'success': False,
                    'error': f'Ya existe un préstamo activo para {tool_name} asignado a {worker_name}'
                }

            if tool.quantity >= quantity:
                if active_loan and (is_renewal or is_assigned):
                    # Actualizar el préstamo existente
                    active_loan.returnLoanDate = new_expiration_date
                    active_loan.save()
                else:
                    # Crear un nuevo préstamo
                    new_loan = ToolLoan(
                        worker=worker,
                        workerPosition=worker_position,
                        workerDni=worker_dni,
                        loanDate=loan_date,
                        returnLoanDate=new_expiration_date,
                        loanAmount=quantity,
                        tool=tool,
                        loanStatus=False
                    )
                    new_loan.save()
                    tool.quantity -= quantity
                    tool.save()
            else:
                return {'success': False, 'error': 'Cantidad insuficiente disponible'}

            return {'success': True, 'message': f'Préstamo para {tool_name} procesado con éxito'}

        except Tool.DoesNotExist:
            return {'success': False, 'error': f'Herramienta {tool_name} no encontrada'}
        except Worker.DoesNotExist:
            return {'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'}

    except Exception as e:
        print(f"Error procesando préstamo: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
        return {'success': False, 'error': str(e)}

@csrf_exempt
def confirm_tool_loan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            work_order = data.get('workOrder')
            loan_date_str = data.get('loanDate')
            return_loan_date_str = data.get('returnLoanDate')
            worker_dni = data.get('workerDni')
            worker_position = data.get('workerPosition')
            manager = data.get('manager', '')
            tool_loans = data.get('tool_loans', [])

            responses = []

            if not return_loan_date_str:
                responses.append({'success': False, 'error': 'Falta la fecha de retorno'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            try:
                loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
                return_loan_date = datetime.strptime(return_loan_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                responses.append({'success': False, 'error': 'Fecha de préstamo o retorno no válida'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            if worker_dni is None or worker_dni.strip() == "":
                responses.append({'success': False, 'error': 'DNI del trabajador no proporcionado'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            try:
                worker = Worker.objects.get(dni=worker_dni)
            except Worker.DoesNotExist:
                responses.append({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)


            if not tool_loans:
                return JsonResponse({'success': False, 'error': 'No se proporcionaron préstamos de herramientas'}, status=400)

            for loan in tool_loans:
                try:
                    tool_name = loan.get('name')
                    quantity = int(loan.get('quantity'))

                    if not tool_name or not quantity:
                        responses.append({'success': False, 'error': 'Datos de herramienta incompletos'})
                        continue

                    tool = Tool.objects.get(name=tool_name)

                    if tool.quantity >= quantity:
                        new_loan = ToolLoan(
                            worker=worker,
                            workerPosition=worker_position,
                            workerDni=worker_dni,
                            loanDate=loan_date,
                            returnLoanDate=return_loan_date,
                            loanAmount=quantity,
                            tool=tool,
                            loanStatus=False,
                            workOrder=work_order
                        )
                        new_loan.save()

                        # Crear registro en History
                        History.objects.create(
                            content_type=ContentType.objects.get_for_model(new_loan),
                            object_name=tool.name,
                            action='Loan Created',
                            user=request.user,  # Asegúrate de que el usuario esté autenticado
                            timestamp=timezone.now()
                        )

                        tool.quantity -= quantity
                        tool.save()

                        responses.append({'success': True, 'message': f'Préstamo para {tool_name} procesado con éxito'})
                    else:
                        responses.append({'success': False, 'error': f'Cantidad insuficiente disponible para {tool_name}'})

                except Tool.DoesNotExist:
                    responses.append({'success': False, 'error': f'Herramienta {tool_name} no encontrada'})
                except Exception as e:
                    print(f"Error procesando préstamo de herramienta: {str(e)}")
                    responses.append({'success': False, 'error': str(e)})

            if any(not r['success'] for r in responses):
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            return JsonResponse({'success': True, 'messages': responses})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)
        except Exception as e:
            print(f"Error general: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

#EQUIPMENTLOAN
@login_required
def equipment_loan_list(request):
    query = request.GET.get('q', '')
    dni_query = request.GET.get('dni', '')

    if query and dni_query:
        # Filtrar por nombre y DNI
        equipment_loans = EquipmentLoan.objects.filter(
            worker__name__icontains=query,
            worker__dni__icontains=dni_query
        )
    elif query:
        # Filtrar solo por nombre
        equipment_loans = EquipmentLoan.objects.filter(worker__name__icontains=query)
    elif dni_query:
        # Filtrar solo por DNI
        equipment_loans = EquipmentLoan.objects.filter(worker__dni__icontains=dni_query)
    else:
        # No hay filtros aplicados
        equipment_loans = EquipmentLoan.objects.all()

    context = {
        'equipment_loans': equipment_loans,
        'query': query,
        'dni_query': dni_query,
    }
    return render(request, 'equipment_loan_list.html', context)

login_required
def add_equipment_loan(request):
    query = request.GET.get('q', '')
    if query:
        equipments = Equipment.objects.filter(name__icontains=query)
    else:
        equipments = Equipment.objects.all()
    if request.method == 'POST':
        form = EquipmentLoanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo de equipos añadido con éxito.')
            return redirect('add_equipment_loan')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = EquipmentLoanForm()
    
    context = {
        'form': form,
        'equipments': equipments,
        'query': query
    }

    return render(request, 'add_equipment_loan.html', context)

@require_http_methods(["GET", "POST"])
def equipment_loan_form(request):
    if request.method == 'POST':
        form = EquipmentLoanForm(request.POST)
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
            equipment_name = cleaned_data['equipment']
            try:
                equipment = Equipment.objects.get(name=equipment_name)
            except Equipment.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Equipo no encontrado'
                }, status=400)

            # Construimos la respuesta JSON
            response_data = {
                'success': True,
                'data': {
                    'worker': worker.name,
                    'workerPosition': cleaned_data['workerPosition'],
                    'workerDni': worker.dni,
                    'loanStatus': equipment.loanStatus,
                    'loanDate': cleaned_data['loanDate'].strftime('%Y-%m-%d'),
                    'returnLoanDate': cleaned_data['returnLoanDate'].strftime('%Y-%m-%d'),
                    'equipment': equipment.name,
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
def check_equipment_availability(request):
    equipment_name = request.GET.get('equipment_name')

    try:
        equipment = Equipment.objects.get(name=equipment_name)
        quantity = equipment.quantity

        can_assign = quantity > 0
        message = '' if can_assign else 'No hay suficiente cantidad disponible.'

        response = {
            'can_assign': can_assign,
            'available': quantity,
            'message': message
        }
    except Equipment.DoesNotExist:
        response = {
            'can_assign': False,
            'available': 0,
            'message': 'Equipo no encontrado.'
        }

    return JsonResponse(response)

def process_equipment_loan(loan):
    try:
        equipment_name = loan.get('name')
        worker_data = loan.get('worker', {})
        worker_name = worker_data.get('name')
        worker_position = worker_data.get('position')
        worker_dni = worker_data.get('dni')
        loan_date_str = loan.get('loanDate')
        quantity = int(loan.get('quantity'))
        is_renewal = loan.get('isRenewal', False)
        is_assigned = loan.get('isAssigned', False)

        # Verificar y convertir la fecha del préstamo
        try:
            loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return {'success': False, 'error': 'Fecha de préstamo no válida'}

        if worker_dni is None or worker_dni.strip() == "":
            return {'success': False, 'error': 'DNI del trabajador no proporcionado'}

        try:
            equipment = Tool.objects.get(name=equipment_name)
            worker = Worker.objects.get(dni=worker_dni)

            # Calcular la nueva fecha de expiración (si aplica)
            new_expiration_date = loan_date + timedelta(days=equipment.duration)

            # Verificar si ya existe un préstamo activo
            active_loan = EquipmentLoan.objects.filter(
                equipment=equipment,
                worker=worker,
                loanDate__lte=loan_date,
                returnLoanDate__gte=loan_date
            ).first()

            if active_loan and not (is_renewal or is_assigned):
                return {
                    'success': False,
                    'error': f'Ya existe un préstamo activo para {equipment_name} asignado a {worker_name}'
                }

            if equipment.quantity >= quantity:
                if active_loan and (is_renewal or is_assigned):
                    # Actualizar el préstamo existente
                    active_loan.returnLoanDate = new_expiration_date
                    active_loan.save()
                else:
                    # Crear un nuevo préstamo
                    new_loan = EquipmentLoan(
                        worker=worker,
                        workerPosition=worker_position,
                        workerDni=worker_dni,
                        loanDate=loan_date,
                        returnLoanDate=new_expiration_date,
                        loanAmount=quantity,
                        equipment=equipment,
                        loanStatus=False
                    )
                    new_loan.save()
                    equipment.quantity -= quantity
                    equipment.save()
            else:
                return {'success': False, 'error': 'Cantidad insuficiente disponible'}

            return {'success': True, 'message': f'Préstamo para {equipment_name} procesado con éxito'}

        except Equipment.DoesNotExist:
            return {'success': False, 'error': f'Herramienta {equipment_name} no encontrada'}
        except Worker.DoesNotExist:
            return {'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'}

    except Exception as e:
        print(f"Error procesando préstamo: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
        return {'success': False, 'error': str(e)}

@csrf_exempt
def confirm_equipment_loan(request):
    if request.method == 'POST':
        try:
            # Parsear los datos JSON
            data = json.loads(request.body)
            print("Datos recibidos:", json.dumps(data, indent=2))  # Depuración mejorada

            # Obtener los datos del formulario
            work_order = data.get('workOrder')
            loan_date_str = data.get('loanDate')
            return_loan_date_str = data.get('returnLoanDate')
            worker_dni = data.get('workerDni')
            worker_name = data.get('worker')
            worker_position = data.get('workerPosition')
            equipment_loans = data.get('equipment_loans', [])

            responses = []

            # Verificar la presencia de la fecha de retorno
            if not return_loan_date_str:
                responses.append({'success': False, 'error': 'Falta la fecha de retorno'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            # Verificar y convertir las fechas
            try:
                loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
                return_loan_date = datetime.strptime(return_loan_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                responses.append({'success': False, 'error': 'Fecha de préstamo o retorno no válida'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            if worker_dni is None or worker_dni.strip() == "":
                responses.append({'success': False, 'error': 'DNI del trabajador no proporcionado'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            try:
                worker = Worker.objects.get(dni=worker_dni)
            except Worker.DoesNotExist:
                responses.append({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            if not equipment_loans:
                return JsonResponse({'success': False, 'error': 'No se proporcionaron préstamos de equipos'}, status=400)

            # Procesar cada préstamo de herramienta
            for loan in equipment_loans:
                try:
                    equipment_name = loan.get('name')
                    quantity = int(loan.get('quantity'))

                    if not equipment_name or not quantity:
                        responses.append({'success': False, 'error': 'Datos de equipos incompletos'})
                        continue

                    # Buscar la herramienta y el trabajador
                    equipment = Equipment.objects.get(name=equipment_name)

                    # Verificar cantidad disponible
                    if equipment.quantity >= quantity:
                        # Crear un nuevo préstamo de herramienta
                        new_loan = EquipmentLoan(  # Cambiar a EquipmentLoan u otro modelo adecuado
                            worker=worker,
                            workerPosition=worker_position,
                            workerDni=worker_dni,
                            loanDate=loan_date,
                            returnLoanDate=return_loan_date,
                            loanAmount=quantity,
                            equipment=equipment,
                            loanStatus=False,
                            workOrder=work_order
                        )
                        new_loan.save()
                        History.objects.create(
                            content_type=ContentType.objects.get_for_model(new_loan),
                            object_name=equipment.name,
                            action='Loan Created',
                            user=request.user,
                            timestamp=timezone.now()
                        )

                        # Actualizar cantidad de herramienta
                        equipment.quantity -= quantity
                        equipment.save()

                        responses.append({'success': True, 'message': f'Préstamo para {equipment_name} procesado con éxito'})
                    else:
                        responses.append({'success': False, 'error': f'Cantidad insuficiente disponible para {equipment_name}'})

                except Equipment.DoesNotExist:
                    responses.append({'success': False, 'error': f'Equipo {equipment_name} no encontrado'})
                except Worker.DoesNotExist:
                    responses.append({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})
                except Exception as e:
                    print(f"Error procesando préstamo de equipo: {str(e)}")
                    responses.append({'success': False, 'error': str(e)})

            if any(not r['success'] for r in responses):
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            return JsonResponse({'success': True, 'messages': responses})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)
        except Exception as e:
            print(f"Error general: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


#MATERIALLOAN
@login_required
def material_loan_list(request):
    query = request.GET.get('q', '')
    dni_query = request.GET.get('dni', '')

    if query and dni_query:
        # Filtrar por nombre y DNI
        material_loans = MaterialLoan.objects.filter(
            worker__name__icontains=query,
            worker__dni__icontains=dni_query
        )
    elif query:
        # Filtrar solo por nombre
        material_loans = MaterialLoan.objects.filter(worker__name__icontains=query)
    elif dni_query:
        # Filtrar solo por DNI
        material_loans = MaterialLoan.objects.filter(worker__dni__icontains=dni_query)
    else:
        # No hay filtros aplicados
        material_loans = MaterialLoan.objects.all()

    return render(request, 'material_loan_list.html', {'material_loans': material_loans, 'query': query, 'dni_query': dni_query})

login_required
def add_material_loan(request):
    query = request.GET.get('q', '')
    if query:
        materials = Material.objects.filter(name__icontains=query)
    else:
        materials = Material.objects.all()
    if request.method == 'POST':
        form = (request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo de material añadido con éxito.')
            return redirect('add_material_loan')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = MaterialLoanForm()
    
    context = {
        'form': form,
        'materials': materials,
        'query': query
    }
    return render(request, 'add_material_loan.html', context)

@require_http_methods(["GET", "POST"])
def material_loan_form(request):
    if request.method == 'POST':
        form = MaterialLoanForm(request.POST)
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

            # Obtenemos la Herramienta
            material_name = cleaned_data['material']
            try:
                material = Material.objects.get(name=material_name)
            except Material.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Material no encontrado'
                }, status=400)

            # Construimos la respuesta JSON
            response_data = {
                'success': True,
                'data': {
                    'worker': worker.name,
                    'workerPosition': cleaned_data['workerPosition'],
                    'workerDni': worker.dni,
                    'loanStatus': material.loanStatus,
                    'loanDate': cleaned_data['loanDate'].strftime('%Y-%m-%d'),
                    'returnLoanDate': cleaned_data['returnLoanDate'].strftime('%Y-%m-%d'),
                    'material': material.name,
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
def check_material_availability(request):
    material_name = request.GET.get('material_name')

    try:
        material = Material.objects.get(name=material_name)
        quantity = material.quantity

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

def process_material_loan(loan):
    try:
        material_name = loan.get('name')
        worker_data = loan.get('worker', {})
        worker_name = worker_data.get('name')
        worker_position = worker_data.get('position')
        worker_dni = worker_data.get('dni')
        loan_date_str = loan.get('loanDate')
        quantity = int(loan.get('quantity'))
        is_renewal = loan.get('isRenewal', False)
        is_assigned = loan.get('isAssigned', False)

        # Verificar y convertir la fecha del préstamo
        try:
            loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return {'success': False, 'error': 'Fecha de préstamo no válida'}

        if worker_dni is None or worker_dni.strip() == "":
            return {'success': False, 'error': 'DNI del trabajador no proporcionado'}

        try:
            material = Material.objects.get(name=material_name)
            worker = Worker.objects.get(dni=worker_dni)

            # Calcular la nueva fecha de expiración (si aplica)
            new_expiration_date = loan_date + timedelta(days=material.duration)

            # Verificar si ya existe un préstamo activo
            active_loan = MaterialLoan.objects.filter(
                material=material,
                worker=worker,
                loanDate__lte=loan_date,
                returnLoanDate__gte=loan_date
            ).first()

            if active_loan and not (is_renewal or is_assigned):
                return {
                    'success': False,
                    'error': f'Ya existe un préstamo activo para {material_name} asignado a {worker_name}'
                }

            if material.quantity >= quantity:
                if active_loan and (is_renewal or is_assigned):
                    # Actualizar el préstamo existente
                    active_loan.returnLoanDate = new_expiration_date
                    active_loan.save()
                else:
                    # Crear un nuevo préstamo
                    new_loan = MaterialLoan(
                        worker=worker,
                        workerPosition=worker_position,
                        workerDni=worker_dni,
                        loanDate=loan_date,
                        returnLoanDate=new_expiration_date,
                        loanAmount=quantity,
                        material=material,
                        loanStatus=False
                    )
                    new_loan.save()
                    material.quantity -= quantity
                    material.save()
            else:
                return {'success': False, 'error': 'Cantidad insuficiente disponible'}

            return {'success': True, 'message': f'Préstamo para {material_name} procesado con éxito'}

        except Tool.DoesNotExist:
            return {'success': False, 'error': f'Material {material_name} no encontrada'}
        except Worker.DoesNotExist:
            return {'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'}

    except Exception as e:
        print(f"Error procesando préstamo: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
        return {'success': False, 'error': str(e)}
    
@csrf_exempt
def confirm_material_loan(request):
    if request.method == 'POST':
        try:
            # Parsear los datos JSON
            data = json.loads(request.body)
            print("Datos recibidos:", json.dumps(data, indent=2))  # Depuración mejorada

            # Obtener los datos del formulario
            work_order = data.get('workOrder')
            loan_date_str = data.get('loanDate')
            worker_dni = data.get('workerDni')
            worker_name = data.get('worker')
            worker_position = data.get('workerPosition')
            manager = data.get('manager', '')
            material_loans = data.get('material_loans', [])

            responses = []

            # Verificar y convertir las fechas
            try:
                loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                responses.append({'success': False, 'error': 'Fecha de préstamo no válida'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            if worker_dni is None or worker_dni.strip() == "":
                responses.append({'success': False, 'error': 'DNI del trabajador no proporcionado'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            try:
                worker = Worker.objects.get(dni=worker_dni)
            except Worker.DoesNotExist:
                responses.append({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})
                return JsonResponse({'success': False, 'errors': responses}, status=400)
            
            if not material_loans:
                return JsonResponse({'success': False, 'error': 'No se proporcionaron préstamos de materiales'}, status=400)

            # Procesar cada préstamo de material
            for loan in material_loans:
                try:
                    material_name = loan.get('name')
                    quantity = int(loan.get('quantity'))

                    if not material_name or not quantity:
                        responses.append({'success': False, 'error': 'Datos de material incompletos'})
                        continue

                    # Buscar el material
                    material = Material.objects.get(name=material_name)

                    # Verificar cantidad disponible
                    if material.quantity >= quantity:
                        # Crear un nuevo préstamo de material
                        new_loan = MaterialLoan(
                            worker=worker,
                            workerPosition=worker_position,
                            workerDni=worker_dni,
                            loanDate=loan_date,
                            loanAmount=quantity,
                            material=material,
                            workOrder=work_order
                        )
                        new_loan.save()

                        History.objects.create(
                            content_type=ContentType.objects.get_for_model(MaterialLoan),
                            object_name=material.name,
                            action='Loan Created',
                            user=request.user,
                            timestamp=timezone.now()
                        )

                        # Actualizar cantidad de material
                        material.quantity -= quantity
                        material.save()

                        responses.append({'success': True, 'message': f'Préstamo para {material_name} procesado con éxito'})
                    else:
                        responses.append({'success': False, 'error': f'Cantidad insuficiente disponible para {material_name}'})

                except Material.DoesNotExist:
                    responses.append({'success': False, 'error': f'Material {material_name} no encontrado'})
                except Exception as e:
                    print(f"Error procesando préstamo de material: {str(e)}")
                    responses.append({'success': False, 'error': str(e)})

            if any(not r['success'] for r in responses):
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            return JsonResponse({'success': True, 'messages': responses})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)
        except Exception as e:
            print(f"Error general: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


#PPELOAN
@login_required
def ppe_loan_list(request):
    query = request.GET.get('q', '')
    dni_query = request.GET.get('dni', '')

    if query and dni_query:
        # Filtrar por nombre y DNI
        ppe_loans = PpeLoan.objects.filter(
            worker__name__icontains=query,
            worker__dni__icontains=dni_query
        )
    elif query:
        # Filtrar solo por nombre
        ppe_loans = PpeLoan.objects.filter(worker__name__icontains=query)
    elif dni_query:
        # Filtrar solo por DNI
        ppe_loans = PpeLoan.objects.filter(worker__dni__icontains=dni_query)
    else:
        # No hay filtros aplicados
        ppe_loans = PpeLoan.objects.all()

    return render(request, 'ppe_loan_list.html', {'ppe_loans': ppe_loans, 'query': query, 'dni_query': dni_query})

@login_required
def add_ppe_loan(request):
    query = request.GET.get('q', '')
    if query:
        ppes = Ppe.objects.filter(name__icontains=query)
    else:
        ppes = Ppe.objects.all()
    if request.method == 'POST':
        form = PpeLoanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_ppe_loan')
    else:
        form = PpeLoanForm()

        context = {
            'form': form,
            'ppes': ppes,
            'query': query
        }
    return render(request, 'add_ppe_loan.html', context)

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
        term = request.GET.get('term')
        qs = Worker.objects.filter(dni__icontains=term)
        dnis = list(qs.values_list('dni', flat=True))
        # Convertir los DNIs a cadenas de texto si no lo son
        dnis = [str(dni) for dni in dnis]
        return JsonResponse(dnis, safe=False)
    return JsonResponse([], safe=False)

def worker_details(request):
    if 'worker_dni' in request.GET:
        try:
            worker = Worker.objects.get(dni=request.GET.get('worker_dni'))
        except Worker.DoesNotExist:
            return JsonResponse({}, status=404)  # No encontrado
    elif 'worker_name' in request.GET:
        try:
            worker = Worker.objects.get(name=request.GET.get('worker_name'))
        except Worker.DoesNotExist:
            return JsonResponse({}, status=404)  # No encontrado
    else:
        return JsonResponse({}, status=400)  # Solicitud inválida
    
    return JsonResponse({
        'name': worker.name,
        'dni': worker.dni,
        'position': worker.position
    })

@require_GET
def check_ppe_availability(request):
    ppe_name = request.GET.get('ppe_name')
    ppe_loan_amount = request.GET.get('ppe_loan_amount')

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        try:
            loan_amount = int(ppe_loan_amount)
        except (ValueError, TypeError):
            return JsonResponse({
                'can_assign': False,
                'available': ppe.quantity,
                'message': 'Cantidad de préstamo inválida.'
            })

        can_assign = (ppe.quantity > 0 and loan_amount <= ppe.quantity)
        message = '' if can_assign else 'No hay suficiente cantidad disponible.'

        response = {
            'can_assign': can_assign,
            'available': ppe.quantity,
            'amount': loan_amount,
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
    loan_date_str = request.GET.get('loan_date')

    if not ppe_name or not loan_date_str:
        return JsonResponse({'success': False, 'message': 'Se requieren nombre de EPP y fecha de préstamo'}, status=400)

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
        expiration_date = loan_date + timedelta(days=ppe.duration)
        return JsonResponse({
            'success': True,
            'duration': ppe.duration,
            'expiration_date': expiration_date.strftime('%Y-%m-%d')
        })
    except Ppe.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'EPP no encontrado.'
        }, status=404)
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Formato de fecha inválido.'
        }, status=400)

@require_GET
def check_ppe_loan_duration(request):
    ppe_name = request.GET.get('ppe_name')
    worker = request.GET.get('worker')
    loan_date = request.GET.get('loan_date')

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        worker_obj = Worker.objects.get(name=worker)

        loan_date = datetime.strptime(loan_date, '%Y-%m-%d').date()
        expiration_date = loan_date + timedelta(days=ppe.duration)

        active_loan = PpeLoan.objects.filter(
            ppe=ppe,
            worker=worker_obj,
            loanDate__lte=expiration_date,
            expirationDate__gte=loan_date
        ).exists()

        if active_loan:
            response = {
                'can_assign': False,
                'message': 'Este trabajador ya tiene una asignación activa para este EPP.'
            }
    except Ppe.DoesNotExist:
        response = {
            'can_assign': False,
            'message': 'EPP no encontrado.'
        }
    except Worker.DoesNotExist:
        response = {
            'can_assign': False,
            'message': 'Trabajador no encontrado.'
        }

    return JsonResponse(response)

@require_GET
def check_ppe_renewal(request):
    ppe_name = request.GET.get('ppe_name')
    worker_name = request.GET.get('worker')
    loan_date = datetime.strptime(request.GET.get('loan_date'), '%Y-%m-%d').date()

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        worker = Worker.objects.get(name=worker_name)
        
        # Verifica si hay asignaciones activas
        active_loan = PpeLoan.objects.filter(
            ppe=ppe,
            worker=worker,
            loanDate__lte=loan_date,
            expirationDate__gte=loan_date
        ).first()

        if active_loan:
            # Hay una asignación activa
            response = {
                'can_assign': False,
                'expiration_date': active_loan.expirationDate.isoformat(),
                'message': 'Este trabajador ya tiene una asignación activa para este EPP.'
            }
        else:
            # No hay asignación activa, pero verifica si ha pasado suficiente tiempo desde la última asignación
            last_loan = PpeLoan.objects.filter(
                ppe=ppe,
                worker=worker,
                loanDate__lt=loan_date
            ).order_by('-loanDate').first()

            if last_loan and (loan_date - last_loan.loanDate).days <= ppe.duration:
                # No ha pasado suficiente tiempo desde la última asignación
                response = {
                    'can_assign': False,
                    'expiration_date': (last_loan.loanDate + timedelta(days=ppe.duration)).isoformat(),
                    'message': f'Debe esperar al menos {ppe.duration} días desde la última asignación.'
                }
            else:
                # Se puede asignar normalmente
                response = {
                    'can_assign': True,
                    'message': 'El EPP está disponible para asignar.'
                }
    except Ppe.DoesNotExist:
        response = {
            'can_assign': False,
            'message': 'EPP no encontrado.'
        }
    except Worker.DoesNotExist:
        response = {
            'can_assign': False,
            'message': 'Trabajador no encontrado.'
        }
    except Exception as e:
        response = {
            'can_assign': False,
            'message': f'Error inesperado: {str(e)}'
        }

    return JsonResponse(response)

@csrf_exempt
def confirm_ppe_loan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ppe_loans = data.get('ppe_loans', [])
            responses = []
            created_or_updated_loans = []

            for loan in ppe_loans:
                try:
                    ppe_name = loan.get('name')
                    worker_data = loan.get('worker', {})
                    worker_name = worker_data.get('name')
                    worker_position = worker_data.get('position')
                    worker_dni = worker_data.get('dni')
                    loan_date_str = loan.get('loanDate')
                    quantity = int(loan.get('quantity'))
                    is_renewal = loan.get('isRenewal', False)
                    is_assigned = loan.get('isAssigned', False)
                    deserve_renewal = loan.get('deserveRenewal', False)
                    is_exception = loan.get('isException', False)
                    comments = loan.get('comments', '')
                    
                    # Verificar y convertir la fecha del préstamo
                    try:
                        loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        responses.append({'success': False, 'error': 'Fecha de préstamo no válida'})
                        continue

                    if worker_dni is None or worker_dni.strip() == "":
                        responses.append({'success': False, 'error': 'DNI del trabajador no proporcionado'})
                        continue

                    try:
                        ppe = Ppe.objects.get(name=ppe_name)
                        worker = Worker.objects.get(dni=worker_dni)

                        # Calcular la nueva fecha de expiración
                        new_expiration_date = loan_date + timedelta(days=ppe.duration)

                        # Verificar si ya existe un préstamo activo (solo para renovaciones)
                        active_loan = None
                        if is_renewal:
                            active_loan = PpeLoan.objects.filter(
                                ppe=ppe,
                                worker=worker,
                                loanDate__lte=loan_date,
                                expirationDate__gte=loan_date
                            ).first()

                        if is_renewal and not active_loan:
                            responses.append({
                                'success': False, 
                                'error': f'No se encontró un préstamo activo para renovar {ppe_name} asignado a {worker_name}'
                            })
                            continue

                        if deserve_renewal or is_exception:
                            if active_loan:
                                # Actualizar el préstamo existente
                                active_loan.expirationDate = new_expiration_date
                                active_loan.comments = comments
                                active_loan.save()
                                created_or_updated_loans.append(active_loan)
                            else:
                                # Crear un nuevo préstamo
                                new_loan = PpeLoan(
                                    worker=worker,
                                    workerPosition=worker_position,
                                    workerDni=worker_dni,
                                    loanDate=loan_date,
                                    expirationDate=new_expiration_date,
                                    loanAmount=quantity,
                                    ppe=ppe,
                                    confirmed=True,
                                    comments=comments
                                )
                                new_loan.save()
                                created_or_updated_loans.append(new_loan)
                                History.objects.create(
                                    content_type=ContentType.objects.get_for_model(PpeLoan),
                                    object_name=ppe.name,
                                    action='Loan Created' if not is_assigned else 'Loan Assigned',
                                    user=request.user,
                                    timestamp=timezone.now()
                                )
                                if not is_renewal:
                                    ppe.quantity -= quantity
                                    ppe.save()
                        else:
                            responses.append({'success': False, 'error': f'Cantidad insuficiente disponible para {ppe_name}'})
                            continue

                    except Ppe.DoesNotExist:
                        responses.append({'success': False, 'error': f'EPP {ppe_name} no encontrado'})
                        continue
                    except Worker.DoesNotExist:
                        responses.append({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})
                        continue

                except Exception as e:
                    print(f"Error procesando préstamo: {str(e)}")
                    print(f"Traceback: {traceback.format_exc()}")  # Imprime el traceback completo
                    responses.append({'success': False, 'error': str(e)})

            if any(not r['success'] for r in responses):
                return JsonResponse({'success': False, 'errors': responses}, status=400)

            # Serializar los préstamos creados o actualizados
            serialized_loans = [
                {
                    'worker_dni': loan.workerDni,
                    'worker_name': loan.worker.name,
                    'worker_surname': loan.worker.surname,
                    'ppe_name': loan.ppe.name,
                    'loan_amount': loan.loanAmount,
                    'loan_date': loan.loanDate.strftime('%Y-%m-%d'),
                    'expiration_date': loan.expirationDate.strftime('%Y-%m-%d')
                }
                for loan in created_or_updated_loans
            ]

            return JsonResponse({'success': True, 'messages': responses, 'created_loans': serialized_loans})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)
        except Exception as e:
            print(f"Error general: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@require_GET
def check_ppe_assignment(request):
    ppe_name = request.GET.get('ppe_name')
    worker_dni = request.GET.get('worker_dni')
    loan_date_str = request.GET.get('loan_date')

    if not ppe_name or not worker_dni or not loan_date_str:
        return JsonResponse({'error': 'Se requieren nombre de EPP, DNI del trabajador y fecha de préstamo'}, status=400)

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
    except Ppe.DoesNotExist:
        return JsonResponse({'error': 'EPP no encontrado'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)

    # Buscar préstamos activos para este EPP y trabajador
    active_loan = PpeLoan.objects.filter(
        ppe=ppe,
        workerDni=worker_dni,
        loanDate__lte=loan_date,
        expirationDate__gte=loan_date,
        confirmed=True
    ).first()

    is_assigned = active_loan is not None
    deserve_renewal = not is_assigned or active_loan.expirationDate <= loan_date

    return JsonResponse({
        'is_assigned': is_assigned,
        'deserve_renewal': deserve_renewal,
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

@login_required
def delete_ppe_loan(request, id):
    ppe_loans = get_object_or_404(PpeLoan, idPpeLoan=id)
    
    if request.method == 'POST':
        ppe_loans.delete()
        History.objects.create(
            content_type=ContentType.objects.get_for_model(PpeLoan),
            object_name=PpeLoan.name,
            action='Loan Delete',
            user=request.user,
            timestamp=timezone.now()
        )
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
            History.objects.create(
                content_type=ContentType.objects.get_for_model(PpeLoan),
                object_name=PpeLoan.name,
                action='Modificar Asignacion',
                user=request.user,
                timestamp=timezone.now()
            )
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
        admin = User.objects.filter(first_name__icontains=query)
    else:
        admin = User.objects.all()
    return render(request, 'table_user.html', {'admin': admin, 'query': query})

def exit(request):
    logout(request)
    return redirect('home')