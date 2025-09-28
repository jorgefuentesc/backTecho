# solicitudes/serializers.py
from rest_framework import serializers
from .models import SolicitudAyuda, DocumentoSolicitud, BitacoraSolicitud, EstadoSolicitud
from users.models import CustomUser # Para mostrar info del usuario

class EstadoSolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoSolicitud
        fields = ['est_id', 'est_nombre']

class DocumentoSolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoSolicitud
        fields = '__all__'


class BitacoraSolicitudSerializer(serializers.ModelSerializer):
    usuario_email = serializers.ReadOnlyField(source='usuario.email')

    class Meta:
        model = BitacoraSolicitud
        fields = [
            'bsca_id', 
            'solicitud', 
            'bsca_observacion', 
            'usuario', 
            'usuario_email', # Mostramos el email al leer
            'bsca_fecha_creacion'
        ]
        read_only_fields = ['solicitud'] # La solicitud se asignará desde la URL

# --- Serializers para la Solicitud de Ayuda ---

# Serializer para LEER/LISTAR solicitudes (con todos los detalles)
class SolicitudAyudaListSerializer(serializers.ModelSerializer):
    est_id = EstadoSolicitudSerializer(read_only=True)
    solicitante = serializers.ReadOnlyField(source='solicitante.email')
    documentos = DocumentoSolicitudSerializer(many=True, read_only=True)
    bitacora = BitacoraSolicitudSerializer(many=True, read_only=True)

    class Meta:
        model = SolicitudAyuda
        fields = '__all__'

# Serializer para CREAR solicitudes (más simple)
class SolicitudAyudaCreateSerializer(serializers.ModelSerializer):
    # Campo para recibir los múltiples documentos. No está en el modelo, por eso 'write_only'.
    documentos_data = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = SolicitudAyuda
        # Solo los campos necesarios para crear. El solicitante se tomará del usuario logueado.
        fields = [
            'sca_titulo', 
            'sca_descripcion', 
            'est_id',
            'documentos_data'
        ]