# solicitudes/urls.py
from django.urls import path
from . import views # Importamos todas las vistas del archivo

urlpatterns = [
    path('crear/', views.crear_solicitud, name='crear-solicitud'),
    path('modificar/', views.modificar_solicitud, name='modificar-solicitud'),
    path('filtrar/', views.filtrar_solicitudes, name='filtrar-solicitudes'),
    path('anular/', views.anular_solicitud, name='anular-solicitudes'),
    path('bitacora/crear/', views.crear_registro_bitacora, name='crear-bitacora'),
    path('bitacora/filtrar/', views.filtrar_bitacora_solicitud, name='filtrar-bitacora'),
    path('estado/crear/', views.crea_estado_solicitud, name='crear-estado'),
    path('estado/filtrar/', views.filtra_estado_solicitud, name='filtrar-estado'),
    path('documento/<int:doc_id>/', views.ver_documento, name='visualizar-documento'),
    path('documento/eliminar/', views.eliminar_documento, name='eliminar-documento'),
    path('tipo/crear/', views.crear_tipo_usuario, name='crear-tipo-usuario'),
    path('tipo/ver/', views.ver_tipos_usuario, name='ver-tipo-usuario'),
    path('tipo/usuario/', views.asignar_tipo_usuario, name='ver-tipo-usuario'),
    path('usuario/lista/', views.listar_usuarios, name='ver-tipo-usuario'),
    path('usuario/modificar/', views.modificar_usuario, name='ver-tipo-usuario'),
    # path('documento/ver/', views.obtener_documento, name='obtener-documento'),
    path('usuario/desactivar_usuario/', views.desactivar_usuario, name='desactivar_usuario'),
    path('usuario/activar_usuario/', views.activar_usuario, name='activar_usuario'),
]