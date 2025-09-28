# solicitudes/models.py
from django.db import models
from django.conf import settings

def ruta_archivos_solicitud(instance, filename):
    # El archivo se subirá a MEDIA_ROOT/solicitud_archivos/<id_solicitud>/<filename>
    return f'solicitud_archivos/{instance.solicitud.sca_id}/{filename}'

class EstadoSolicitud(models.Model):
    est_id = models.AutoField(primary_key=True)
    est_nombre = models.CharField(max_length=80) 
    est_vigencia = models.BooleanField(default=True)
    est_fecha_creacion = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.est_nombre

class SolicitudAyuda(models.Model):
    sca_id = models.AutoField(primary_key=True)
    sca_titulo = models.CharField(max_length=200)
    sca_descripcion = models.TextField()
    est_id = models.ForeignKey(EstadoSolicitud,on_delete=models.PROTECT, related_name='solicitudes')
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='solicitudes_creadas')
    sca_fecha_creacion = models.DateTimeField(auto_now_add=True)
    sca_fecha_actualizacion = models.DateTimeField(auto_now=True)
    sca_usuario_actualizacion = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='+')

    def __str__(self):
        return f"Solicitud #{self.sca_id}: {self.sca_titulo}"

class BitacoraSolicitud(models.Model):
    bsca_id = models.AutoField(primary_key=True)
    sca_id = models.ForeignKey(SolicitudAyuda,on_delete=models.CASCADE,related_name='bitacora')
    bsca_observacion = models.TextField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name='entradas_bitacora')
    bsca_fecha_creacion = models.DateTimeField(auto_now_add=True)
    bsca_fecha_actualizacion = models.DateTimeField(auto_now=True)
    bsca_usuario_actualizacion = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='+')

    def __str__(self):
        return f"Registro para Solicitud #{self.sca_id.sca_id} a las {self.bsca_fecha_creacion.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-bsca_fecha_creacion']

class DocumentoSolicitud(models.Model):
    doc_id = models.AutoField(primary_key=True)
    solicitud = models.ForeignKey( SolicitudAyuda, on_delete=models.CASCADE,related_name='documentos' )
    bitacora = models.ForeignKey(BitacoraSolicitud,related_name='documentos',on_delete=models.SET_NULL,null=True,blank=True,)
    doc_archivo = models.FileField(upload_to=ruta_archivos_solicitud)
    doc_fecha_creacion = models.DateTimeField(auto_now_add=True)
    doc_fecha_actualizacion = models.DateTimeField(auto_now=True)
    doc_usuario_actualizacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,null=True,blank=True,related_name='+')

    def __str__(self):
        return f"Documento para Solicitud #{self.solicitud.sca_id}"