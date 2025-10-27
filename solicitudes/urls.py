# solicitudes/urls.py
from django.urls import path
from . import views # Importamos todas las vistas del archivo

urlpatterns = [
    path('crear/', views.crear_solicitud, name='crear-solicitud'),
    path('modificar/', views.modificar_solicitud, name='modificar-solicitud'),
    path('filtrar/', views.filtrar_solicitudes, name='filtrar-solicitudes'),
    path('bitacora/crear/', views.crear_registro_bitacora, name='crear-bitacora'),
    path('bitacora/filtrar/', views.filtrar_bitacora_solicitud, name='filtrar-bitacora'),
    path('estado/crear/', views.crea_estado_solicitud, name='crear-estado'),
    path('estado/filtrar/', views.filtra_estado_solicitud, name='filtrar-estado'),
    path('documento/<int:doc_id>/', views.ver_documento, name='visualizar-documento'),
    path('documento/eliminar/', views.eliminar_documento, name='eliminar-documento'),
    # path('documento/ver/', views.obtener_documento, name='obtener-documento'),
]