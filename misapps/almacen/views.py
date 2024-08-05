from django.shortcuts import render, redirect
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
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
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import IntegrityError
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
from .models.PpeLoan import PpeLoan
from .models.Equipment import Equipment
from .models.Worker import Worker
from .models.Material import Material
from .models.Loan import Loan
from .models.Tool import Tool
from .models.History import History
from .models.Unit import Unit
from .models.PpeStockUpdate import PpeStockUpdate
from .forms import AdminSignUpForm, PpeForm, MaterialForm, WorkerForm, EquipmentForm, ToolForm, LoanForm, PpeLoanForm, Ppe, CreatePpeForm, CreateMaterialForm, CreateEquipmentForm, CreateToolForm, PpeStockUpdateForm

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

def check_ppe_duration(request):
    ppe_name = request.GET.get('ppe_name')

    try:
        ppe = Ppe.objects.get(name=ppe_name)
        response = {
            'success': True,
            'duration': ppe.duration
        }
    except Ppe.DoesNotExist:
        response = {
            'success': False,
            'message': 'EPP no encontrado.'
        }

    return JsonResponse(response)

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
    

#Vistaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaas
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
    
@transaction.atomic
def confirm_ppe_loan(request):
    data = json.loads(request.body)
    ppe_loans = data.get('ppe_loans', [])

    for loan in ppe_loans:
        ppe_name = loan.get('name')
        worker_name = loan.get('worker', {}).get('name')
        worker_position = loan.get('workerPosition')
        worker_dni = loan.get('workerDni')
        loan_date_str = loan.get('loanDate')
        quantity = int(loan.get('quantity'))
        is_renewal = loan.get('isRenewal', False)
        is_exception = loan.get('isException', False)
        
        # Verificar y convertir la fecha del préstamo
        try:
            loan_date = datetime.strptime(loan_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': 'Fecha de préstamo no válida'}, status=400)

        try:
            ppe = Ppe.objects.get(name=ppe_name)
            worker = Worker.objects.get(dni=worker_dni)

            # Calcular la nueva fecha de expiración
            new_expiration_date = loan_date + timedelta(days=ppe.duration)

            # Verificar si ya existe un préstamo activo
            active_loan = PpeLoan.objects.filter(
                ppe=ppe,
                worker=worker,
                loanDate__lte=loan_date,
                expirationDate__gte=loan_date
            ).first()

            if active_loan and not (is_renewal or is_exception):
                return JsonResponse({
                    'success': False, 
                    'error': f'Ya existe un préstamo activo para {ppe_name} asignado a {worker_name}'
                })

            if ppe.quantity >= quantity:
                if active_loan and (is_renewal or is_exception):
                    # Actualizar el préstamo existente
                    active_loan.expirationDate = new_expiration_date
                    active_loan.save()
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
                        confirmed=True
                    )
                    new_loan.save()
                    ppe.quantity -= quantity
                    ppe.save()
            else:
                return JsonResponse({'success': False, 'error': 'Cantidad insuficiente disponible'})

        except Ppe.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'EPP {ppe_name} no encontrado'})
        except Worker.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})

    return JsonResponse({'success': True})
    
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

#LOAN
@login_required
def loan_list(request):
    query = request.GET.get('q')
    if query:
        loans = Loan.objects.filter(worker__name__icontains=query)
    else:
        loans = Loan.objects.all()
    return render(request, 'loan_list.html', {'loans': loans, 'query': query})

@login_required
def add_loan(request):
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add_loan')
    else:
        form = LoanForm()
    return render(request, 'add_loan.html', {'form': form})

@login_required
def delete_loan(request, id):
    loans = get_object_or_404(Loan, idLoan=id)
    
    if request.method == 'POST':
        loans.delete()
        return redirect('loan_list')
    else:
        return render(request, 'delete_loan.html', {'loans': loans})
    
@login_required
def modify_loan(request, id):
    loans = get_object_or_404(Loan, idLoan=id)
    form = LoanForm(instance=loans)

    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loans)
        if form.is_valid():
            form.save()
            return redirect('loan_list')
    else:
        return render(request, 'modify_loan.html', {'form': form})
    
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
    if request.method == 'POST':
        form = PpeLoanForm(request.POST)
        if form.is_valid():
            ppe_loan = form.save(commit=False)
            worker_name = form.cleaned_data['worker']
            try:
                worker = Worker.objects.get(name=worker_name)
                ppe_loan.worker = worker
                ppe_loan.save()
                return redirect('some_success_url')
            except Worker.DoesNotExist:
                form.add_error('worker', 'Trabajador no encontrado')
    else:
        form = PpeLoanForm()
    
    # Obtener todos los objetos Ppe
    ppes = Ppe.objects.all()
    
    context = {
        'form': form,
        'ppes': ppes
    }
    return render(request, 'add_ppe_loan.html', context)

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

@csrf_exempt
def confirm_ppe_loan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ppe_loans = data.get('ppe_loans', [])

            for loan in ppe_loans:
                ppe_name = loan.get('name')
                worker = loan.get('worker', {})
                worker_name = worker.get('name')
                worker_dni = worker.get('dni')
                loan_date = datetime.strptime(loan.get('loanDate'), '%Y-%m-%d').date()
                quantity = int(loan.get('quantity'))
                is_renewal = loan.get('isRenewal', False)
                is_exception = loan.get('isException', False)
                new_expiration_date_str = loan.get('newExpirationDate')

                try:
                    ppe = Ppe.objects.get(name=ppe_name)
                    worker = Worker.objects.get(dni=worker_dni)

                    if not new_expiration_date_str:
                        expiration_date = loan_date + timedelta(days=ppe.duration)
                    else:
                        expiration_date = datetime.strptime(new_expiration_date_str, '%Y-%m-%d').date()

                    active_loan = PpeLoan.objects.filter(
                        ppe=ppe,
                        worker=worker,
                        loanDate__lte=loan_date,
                        expirationDate__gte=loan_date
                    ).first()

                    if active_loan and not (is_renewal or is_exception):
                        return JsonResponse({
                            'success': False, 
                            'error': f'Ya existe un préstamo activo para {ppe_name} asignado a {worker_name}'
                        })

                    if ppe.quantity >= quantity:
                        if active_loan and (is_renewal or is_exception):
                            active_loan.expirationDate = expiration_date
                            active_loan.save()
                        else:
                            new_loan = PpeLoan(
                                worker=worker,
                                workerPosition=loan.get('workerPosition'),
                                workerDni=worker_dni,
                                loanDate=loan_date,
                                expirationDate=expiration_date,
                                loanAmount=quantity,
                                ppe=ppe,
                                confirmed=True
                            )
                            new_loan.save()
                            ppe.quantity -= quantity
                            ppe.save()
                    else:
                        return JsonResponse({'success': False, 'error': 'Cantidad insuficiente disponible'})

                except Ppe.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'EPP {ppe_name} no encontrado'})
                except Worker.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Trabajador con DNI {worker_dni} no encontrado'})

            return JsonResponse({'success': True})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})



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