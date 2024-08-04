from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import home, register_admin, login, exit, history
from . import views

urlpatterns = [
    path('', home, name='home'),

    #EPP
    path('ppe/create/', views.create_ppe, name='create_ppe'),
    path('ppe/total/', views.ppe_total, name='ppe_total'),
    path('add_new_unit/', views.add_new_unit, name='add_new_unit'),
    path('get_ppe_data/', views.get_ppe_data, name='get_ppe_data'),
    path('save_all_ppe/', views.save_all_ppe, name='save_all_ppe'),
    path('ppe/create/table/', views.PersonalProtectionEquipment, name='table_created_ppe'),
    path('ppe/cost/ppe/', views.total_cost_ppe, name='total_ppe_cost_table'),
    path('ppe/cost/equip/', views.total_cost_equip, name='total_equip_cost_table'),
    path('ppe/cost/material/', views.total_cost_material, name='total_mat_cost_table'),
    path('ppe/cost/tool/', views.total_cost_tool, name='total_tool_cost_table'),
    path('ppe/cost/table/', views.cost_summary_view, name='total_cost_table'),
    path('ppe/duration/table/', views.show_duration, name='table_duration_ppe'),
    path('update-ppe-duration/', views.update_ppe_duration, name='update_ppe_duration'),
    path('ppe/show/table/', views.set_duration, name='show_duration_table'),
    path('ppe/add/', views.add_ppe, name='add_ppe'),
    path('ppe/add/table/', views.show_added_ppe, name='table_added_ppe'),
    path('ppe/<str:name>/modify/', views.modify_ppe, name='modify_ppe'),
    path('ppe/<str:ppe_name>/delete/', views.delete_ppe, name='delete_ppe'),
    path('ppe/total_ppe_stock/', views.total_ppe_stock, name='total_ppe_stock'),

    #EQUIPOS
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/<str:equipment_name>/delete/', views.delete_equipment, name='delete_equipment'),
    path('equipment/<str:name>/modify/', views.modify_equipment, name='modify_equipment'),
    path('equipment/create/', views.create_equipment, name='create_equipment'),
    path('equipment/total/', views.equipment_total, name='equipment_total'),
    path('equipment/total_equipment_stock/', views.total_equipment_stock, name='total_equipment_stock'),

    #MATERIALES
    path('material/', views.material_list, name='material_list'),
    path('material/create/', views.create_material, name='create_material'),
    path('material/total/', views.material_total, name='material_total'),
    path('material/<str:material_name>/modify/', views.modify_material, name='modify_material'),
    path('material/<str:material_name>/delete/', views.delete_material, name='delete_material'),
    path('materials/total_material_stock/', views.total_material_stock, name='total_material_stock'),

    #HERRAMIENTAS
    path('tool/', views.tool_list, name='tool_list'),
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

    #ASIGNACIONES
    path('loan/', views.loan_list, name='loan_list'),
    path('loan/create/', views.add_loan, name='add_loan'),
    path('loan/delete/<int:id>/', views.delete_loan, name='delete_loan'),
    path('loan/modify/<int:id>/', views.modify_loan, name='modify_loan'),

    #ASIGNACIONES DE EPP
    path('ppeloan/', views.ppe_loan_list, name='ppe_loan_list'),
    path('add_ppe_loan/', views.add_ppe_loan, name='add_ppe_loan'),
    path('check_ppe_duration/', views.check_ppe_duration, name='check_ppe_duration'),
    path('check-ppe-availability/', views.check_ppe_availability, name='check_ppe_availability'),
    path('check-ppe-loan-duration/', views.check_ppe_loan_duration, name='check_ppe_loan_duration'),
    path('worker_autocomplete/', views.worker_autocomplete, name='worker_autocomplete'),
    path('dni_autocomplete/', views.dni_autocomplete, name='dni_autocomplete'),
    path('worker-details/', views.worker_details, name='worker_details'),
    path('load_given_ppe/', views.load_given_ppe, name='load_given_ppe'),
    path('check_ppe_renewal/', views.check_ppe_renewal, name='check_ppe_renewal'),
    path('confirm_ppe_loan/', views.confirm_ppe_loan, name='confirm_ppe_loan'),
    path('ppeloan/delete/<int:id>/', views.delete_ppe_loan, name='delete_ppe_loan'),
    path('ppeloan/modify/<int:id>/', views.modify_ppe_loan, name='modify_ppe_loan'),

    #USUARIOS
    path('register_admin/', register_admin, name='register_admin'),
    path('admin_list/', views.user_list, name='table_user'),
    path('history/', history, name='history'),
    path('login/', login, name='login'),
    path('logout/', exit, name='exit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)