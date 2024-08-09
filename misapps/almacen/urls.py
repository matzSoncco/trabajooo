from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import home, register_admin, login, exit, history
from . import views

urlpatterns = [
    path('', home, name='home'),

    #EPP
    path('ppe/create/', views.create_ppe, name='create_ppe'),
    path('ppe/total/add', views.ppe_total_add, name='ppe_total_add'),
    path('ppe/total/', views.ppe_total, name='ppe_total'),
    path('add_new_unit/', views.add_new_unit, name='add_new_unit'),
    path('get_ppe_data/', views.get_ppe_data, name='get_ppe_data'),
    path('save_all_ppe/', views.save_all_ppe, name='save_all_ppe'),
    path('ppe/cost/ppe/', views.total_cost_ppe, name='total_ppe_cost_table'),
    path('ppe/cost/equip/', views.total_cost_equip, name='total_equip_cost_table'),
    path('ppe/cost/material/', views.total_cost_material, name='total_mat_cost_table'),
    path('ppe/cost/tool/', views.total_cost_tool, name='total_tool_cost_table'),
    path('ppe/cost/table/', views.cost_summary_view, name='total_cost_table'),
    path('update-ppe-duration/', views.update_ppe_duration, name='update_ppe_duration'),
    path('ppe/show/table/', views.set_duration, name='show_duration_table'),
    path('ppe/add/', views.add_ppe, name='add_ppe'),
    path('ppe/<str:name>/modify/', views.modify_ppe, name='modify_ppe'),
    path('ppe/<str:name>/modify_add/', views.modify_ppe_add, name='modify_ppe_add'),
    path('ppe/<str:ppe_name>/delete/', views.delete_ppe, name='delete_ppe'),
    path('ppe/total_ppe_stock/', views.total_ppe_stock, name='total_ppe_stock'),

    #EQUIPOS
    path('get_equipment_data/', views.get_equipment_data, name='get_equipment_data'),
    path('equipment/total/add', views.equipment_total_add, name='equipment_total_add'),
    path('save_all_equipment/', views.save_all_equipment, name='save_all_equipment'),
    path('equipment/<str:equipment_name>/delete/', views.delete_equipment, name='delete_equipment'),
    path('equipment/<str:name>/modify/', views.modify_equipment, name='modify_equipment'),
    path('equipment/create/', views.create_equipment, name='create_equipment'),
    path('equipment/total/', views.equipment_total, name='equipment_total'),
    path('equipment/add/', views.add_equipment, name='add_equipment'),
    path('equipment/total_equipment_stock/', views.total_equipment_stock, name='total_equipment_stock'),

    #MATERIALES
    path('material/add/', views.add_material, name='add_material'),
    path('get_material_data/', views.get_material_data, name='get_material_data'),
    path('material/total/add', views.material_total_add, name='material_total_add'),
    path('save_all_material/', views.save_all_material, name='save_all_material'),
    path('material/create/', views.create_material, name='create_material'),
    path('material/total/', views.material_total, name='material_total'),
    path('material/<str:material_name>/modify/', views.modify_material, name='modify_material'),
    path('material/<str:material_name>/delete/', views.delete_material, name='delete_material'),
    path('materials/total_material_stock/', views.total_material_stock, name='total_material_stock'),

    #HERRAMIENTAS
    path('tool/', views.tool_list, name='tool_list'),
    path('tool/add/', views.add_tool, name='add_tool'),
    path('get_tool_data/', views.get_tool_data, name='get_tool_data'),
    path('save_all_tool/', views.save_all_tools, name='save_all_tools'),
    path('tool/total/add', views.tool_total_add, name='tool_total_add'),
    path('tool/create/', views.create_tool, name='create_tool'),
    path('tool/total/', views.tool_total, name='tool_total'),
    path('tool/<str:tool_name>/delete/', views.delete_tool, name='delete_tool'),
    path('tool/<str:name>/modify/', views.modify_tool, name='modify_tool'),
    path('tool/total_tool_stock/', views.total_tool_stock, name='total_tool_list'),

    #TRABAJADORES
    path('worker/', views.worker_list, name='worker_list'),
    path('worker/create/', views.create_worker, name='create_worker'),
    path('worker/delete/<int:id>/', views.delete_worker, name='delete_worker'),
    path('worker/modify/<int:id>/', views.modify_worker, name='modify_worker'),

    path('worker_autocomplete/', views.worker_autocomplete, name='worker_autocomplete'),
    path('dni_autocomplete/', views.dni_autocomplete, name='dni_autocomplete'),
    path('worker-details/', views.worker_details, name='worker_details'),

    #ASIGNACIONES DE EPP
    path('ppeloan/', views.ppe_loan_list, name='ppe_loan_list'),
    path('add_ppe_loan/', views.add_ppe_loan, name='add_ppe_loan'),
    path('ppe_loan_form/', views.ppe_loan_form, name='ppe_loan_form'),
    path('check-ppe-assignment/', views.check_ppe_assignment, name='check_ppe_assignment'),
    path('check_ppe_duration/', views.check_ppe_duration, name='check_ppe_duration'),
    path('check-ppe-availability/', views.check_ppe_availability, name='check_ppe_availability'),
    path('check-ppe-loan-duration/', views.check_ppe_loan_duration, name='check_ppe_loan_duration'),
    path('confirm_ppe_loan/', views.confirm_ppe_loan, name='confirm_ppe_loan'),
    path('ppeloan/delete/<int:id>/', views.delete_ppe_loan, name='delete_ppe_loan'),
    path('ppeloan/modify/<int:id>/', views.modify_ppe_loan, name='modify_ppe_loan'),

    #ASIGNACIONES DE HERRAMIENTAS
    path('return', views.return_view, name='return'),
    path('return/tool/', views.return_tool_view, name='return_tool'),
    path('tool_loan_list/', views.tool_loan_list, name='tool_loan_list'),
    path('add_tool_loan/', views.add_tool_loan, name='add_tool_loan'),
    path('tool_loan_form/', views.tool_loan_form, name='tool_loan_form'),
    path('confirm_tool_loan/', views.confirm_tool_loan, name='confirm_tool_loan'),
    path('check_tool_availability/', views.check_tool_availability, name='check_tool_availability'),

    #ASIGNACIONES DE EQUIPOS
    path('return/equipment/', views.return_equipment_view, name='return_equipment'),
    path('equipment_loan_list/', views.equipment_loan_list, name='equipment_loan_list'),
    path('add_equipment_loan/', views.add_equipment_loan, name='add_equipment_loan'),
    path('equipment_loan_form/', views.equipment_loan_form, name='equipment_loan_form'),
    path('confirm_equipment_loan/', views.confirm_equipment_loan, name='confirm_equipment_loan'),
    path('check_equipment_availability/', views.check_equipment_availability, name='check_equipment_availability'),

    #ASIGNACIONES DE MATERIALES
    path('material_loan_list/', views.material_loan_list, name='material_loan_list'),
    path('add_material_loan/', views.add_material_loan, name='add_material_loan'),
    path('material_loan_form/', views.material_loan_form, name='material_loan_form'),
    path('confirm_material_loan/', views.confirm_material_loan, name='confirm_material_loan'),
    path('check_material_availability/', views.check_material_availability, name='check_material_availability'),

    #USUARIOS
    path('register_admin/', register_admin, name='register_admin'),
    path('admin_list/', views.user_list, name='table_user'),
    path('history/', history, name='history'),
    path('login/', login, name='login'),
    path('logout/', exit, name='exit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)