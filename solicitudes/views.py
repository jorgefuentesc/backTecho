# solicitudes/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import SolicitudAyuda, DocumentoSolicitud, BitacoraSolicitud, EstadoSolicitud
from users.models import TipoUsuario, CustomUser

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_solicitud(request):

    try:
        titulo = request.data.get('sca_titulo')
        descripcion = request.data.get('sca_descripcion')
        estado_id = request.data.get('est_id')
        documentos = request.FILES.getlist('documentos_data')

        if not titulo or not descripcion or not estado_id:
            return Response(
                {"error": "Los campos 'sca_titulo', 'sca_descripcion' y 'est_id' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )       
        estado = get_object_or_404(EstadoSolicitud, pk=estado_id)

        with transaction.atomic():
            solicitud = SolicitudAyuda.objects.create(
                sca_titulo=titulo,
                sca_descripcion=descripcion,
                est_id=estado,
                solicitante=request.user
            )

            for documento in documentos:
                DocumentoSolicitud.objects.create(solicitud=solicitud, doc_archivo=documento,doc_usuario_actualizacion = request.user)
            
            BitacoraSolicitud.objects.create(
                sca_id=solicitud,
                usuario=request.user,
            )

        response_data = {
            "mensaje": "Solicitud creada correctamente.",
            "solicitud": {
                "sca_id": solicitud.sca_id,
                "sca_titulo": solicitud.sca_titulo,
                "sca_descripcion": solicitud.sca_descripcion,
                "estado": solicitud.est_id.est_nombre,
                "solicitante_email": solicitud.solicitante.email,
                "sca_fecha_creacion": solicitud.sca_fecha_creacion
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    except EstadoSolicitud.DoesNotExist:
        return Response({"error": "El estado de solicitud especificado no existe."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def modificar_solicitud(request):
    try:
        solicitud_id = request.data.get('solicitud_id')
        
        titulo = request.data.get('sca_titulo')
        descripcion = request.data.get('sca_descripcion')
        estado_id = request.data.get('est_id')
        
        nuevos_documentos = request.FILES.getlist('nuevos_documentos')

        if not solicitud_id:
            return Response(
                {"error": "El campo 'solicitud_id' es obligatorio para modificar."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not titulo and not descripcion and not estado_id and not nuevos_documentos:
            return Response(
                {"error": "Debe proporcionar al menos un campo para modificar (sca_titulo, sca_descripcion, est_id) o un archivo en 'nuevos_documentos'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            solicitud = get_object_or_404(SolicitudAyuda, pk=solicitud_id)
            
            observaciones = []

            if titulo:
                solicitud.sca_titulo = titulo
                observaciones.append(f"Título actualizado a: '{titulo}'")
            
            if descripcion:
                solicitud.sca_descripcion = descripcion
                observaciones.append("Descripción actualizada.")
            
            if estado_id:
                nuevo_estado = get_object_or_404(EstadoSolicitud, pk=estado_id)
                solicitud.est_id = nuevo_estado
                observaciones.append(f"Estado cambiado a: '{nuevo_estado.est_nombre}'")

            solicitud.sca_usuario_actualizacion = request.user
            solicitud.save()

            if nuevos_documentos:
                for documento in nuevos_documentos:
                    DocumentoSolicitud.objects.create(
                        solicitud=solicitud, 
                        doc_archivo=documento,
                        doc_usuario_actualizacion=request.user
                    )
                observaciones.append(f"Se añadieron {len(nuevos_documentos)} documento(s) nuevo(s).")

            if observaciones:
                observacion_final = "Solicitud modificada. " + " | ".join(observaciones)
                BitacoraSolicitud.objects.create(
                    sca_id=solicitud,
                    usuario=request.user,
                    bsca_observacion=observacion_final
                )

            docs = []
            for doc in solicitud.documentos.all():
                docs.append({
                    "doc_id": doc.doc_id,
                    "url_archivo": request.build_absolute_uri(doc.doc_archivo.url) if doc.doc_archivo else None,
                    "nombre_archivo": str(doc.doc_archivo.name)
                })

            response_data = {
                "mensaje": "Solicitud actualizada correctamente.",
                "solicitud_actualizada": {
                    "sca_id": solicitud.sca_id,
                    "sca_titulo": solicitud.sca_titulo,
                    "sca_descripcion": solicitud.sca_descripcion,
                    "estado": solicitud.est_id.est_nombre,
                    "sca_fecha_actualizacion": solicitud.sca_fecha_actualizacion,
                    "usuario_actualizacion": solicitud.sca_usuario_actualizacion.email,
                    "documentos": docs
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)

    except SolicitudAyuda.DoesNotExist:
        return Response({"error": "La solicitud que intenta modificar no existe."}, status=status.HTTP_404_NOT_FOUND)
    except EstadoSolicitud.DoesNotExist:
        return Response({"error": "El nuevo estado de solicitud especificado no existe."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al modificar la solicitud.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def filtrar_solicitudes(request):

    try:
        filtros = request.data
        queryset = SolicitudAyuda.objects.all()

        if filtros.get('estado_id'):
            queryset = queryset.filter(est_id=filtros['estado_id'])
        if filtros.get('year'):
            queryset = queryset.filter(sca_fecha_creacion__year=filtros['year'])
        if filtros.get('month'):
            queryset = queryset.filter(sca_fecha_creacion__month=filtros['month'])
        if filtros.get('day'):
            queryset = queryset.filter(sca_fecha_creacion__day=filtros['day'])
        if filtros.get('solicitante_id'):
            queryset = queryset.filter(solicitante_id=filtros['solicitante_id'])
        
        results = []
        for solicitud in queryset:
            docs = []
            for doc in solicitud.documentos.all():
                docs.append({
                    "doc_id": doc.doc_id,
                    "url_archivo": request.build_absolute_uri(doc.doc_archivo.url) if doc.doc_archivo else None
                })
            results.append({
                "sca_id": solicitud.sca_id,
                "id_solicitante": solicitud.solicitante.id,
                'rut'   : solicitud.solicitante.rut,
                'telefono': solicitud.solicitante.telefono,
                "sca_titulo": solicitud.sca_titulo,
                'sca_descripcion':solicitud.sca_descripcion,
                "estado": solicitud.est_id.est_id,
                "solicitante_email": solicitud.solicitante.email,
                "sca_fecha_creacion": solicitud.sca_fecha_creacion,
                "documentos": docs
            })
        
        return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al filtrar las solicitudes.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_registro_bitacora(request):

    try:
        solicitud_id = request.data.get('solicitud_id')
        observacion = request.data.get('bsca_observacion')
        documento_adjunto = request.FILES.get('doc_archivo')

        if not solicitud_id or not observacion:
            return Response(
                {"error": "Los campos 'solicitud_id' y 'bsca_observacion' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        solicitud = get_object_or_404(SolicitudAyuda, pk=solicitud_id)

        with transaction.atomic():
            bitacora = BitacoraSolicitud.objects.create(
                sca_id=solicitud,
                usuario=request.user,
                bsca_usuario_actualizacion=request.user,
                bsca_observacion=observacion
            )
            if documento_adjunto:
                DocumentoSolicitud.objects.create(
                    solicitud=solicitud,
                    bitacora=bitacora,
                    doc_archivo=documento_adjunto
                )
        
        response_data = {
            "mensaje": "Registro de bitácora creado correctamente.",
            "bitacora": {
                "bsca_id": bitacora.bsca_id,
                "solicitud_id": bitacora.sca_id.sca_id,
                "observacion": bitacora.bsca_observacion,
                "usuario_email": bitacora.usuario.email,
                "fecha_creacion": bitacora.bsca_fecha_creacion
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    except SolicitudAyuda.DoesNotExist:
        return Response({"error": "La solicitud especificada no existe."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def filtrar_bitacora_solicitud(request):
    try:
        solicitud_id = request.data.get('solicitud_id')
        if not solicitud_id:
            return Response({"error": "El campo 'solicitud_id' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        
        get_object_or_404(SolicitudAyuda, pk=solicitud_id)
        
        queryset = BitacoraSolicitud.objects.filter(sca_id=solicitud_id)

        results = []
        for registro in queryset:
            docs = []
            for doc in registro.documentos.all():
                 docs.append({
                    "doc_id": doc.doc_id,
                    "url_archivo": request.build_absolute_uri(doc.doc_archivo.url) if doc.doc_archivo else None
                })
            
            results.append({
                "bsca_id": registro.bsca_id,
                "observacion": registro.bsca_observacion,
                "usuario_email": registro.usuario.email if registro.usuario else "Usuario eliminado",
                "fecha_creacion": registro.bsca_fecha_creacion,
                "documentos_adjuntos": docs
            })
        
        return Response(results, status=status.HTTP_200_OK)

    except SolicitudAyuda.DoesNotExist:
        return Response({"error": "La solicitud especificada no existe."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crea_estado_solicitud(request):
    try:
        nombre_estado = request.data.get('nombre_estado')

        if nombre_estado:
            with transaction.atomic():
                crea_nuevo_estado = EstadoSolicitud.objects.create(
                    est_nombre = nombre_estado
                )
            respose = {
                "mensaje": "Registro de bitácora creado correctamente.",
                "estado" : f"Se creo el estado: {nombre_estado} Correctamente."
            }

            return Response(respose, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def filtra_estado_solicitud(request):
    try:
        obj_estados = EstadoSolicitud.objects.all()
        list_estados = []
        for estado in obj_estados:
            list_estados.append({
                "estado_id"     : estado.est_id,
                "estado_nombre" : estado.est_nombre
            })

        respose = {
            "mensaje": "Registro de estados obtenidos correctamente.",
            "estados" : list_estados
        }

        return Response(respose, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ver_documento(request, doc_id):
    try:
        # get_object_or_404 se encarga del error 'DoesNotExist' por sí solo.
        documento = get_object_or_404(DocumentoSolicitud, pk=doc_id)

        ruta_del_archivo = documento.doc_archivo.path
        response = FileResponse(open(ruta_del_archivo, 'rb'))
        return response

    except Exception as e:
        # Solo necesitamos capturar otros errores inesperados.
        return Response(
            {"error": "Ocurrió un error inesperado al obtener el documento.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def eliminar_documento(request):
    try:
        documento_id = request.data.get('doc_id')

        if not documento_id:
            return Response(
                {"error": "El campo 'doc_id' es obligatorio para eliminar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            documento = get_object_or_404(DocumentoSolicitud, pk=documento_id)
            solicitud_asociada = documento.solicitud
            nombre_archivo = str(documento.doc_archivo.name)

            documento.doc_archivo.delete() 
            documento.delete()

            observacion = f"Documento eliminado: '{nombre_archivo}'"
            BitacoraSolicitud.objects.create(
                solicitud=solicitud_asociada,
                usuario=request.user,
                bsca_observacion=observacion
            )

            return Response(
                {"mensaje": "Documento eliminado correctamente.", "documento_eliminado": nombre_archivo},
                status=status.HTTP_200_OK
            )

    except DocumentoSolicitud.DoesNotExist:
        return Response({"error": "El documento que intenta eliminar no existe."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al eliminar el documento.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

def enviar_notificacion_nueva_solicitud(solicitud):
    try:
        solicitante = solicitud.solicitante
        titulo_solicitud = solicitud.sca_titulo

        asunto = f"Hemos recibido tu Solicitud: #{solicitud.sca_id} - {titulo_solicitud}"

        mensaje = f"""
        Estimado(a) {solicitante.first_name},

        Hemos recibido tu solicitud "{titulo_solicitud}" con éxito.
        Tu solicitud ha sido registrada con el estado: "{solicitud.est_id.est_nombre}".

        Pronto nuestro equipo la revisará. Puedes seguir el estado de tu solicitud en la plataforma.

        Atentamente,
        El Equipo de [Nombre de tu Organización]
        """

        email_desde = settings.EMAIL_HOST_USER
        email_para = [solicitante.email] 

        send_mail(
            asunto,
            mensaje,
            email_desde,
            email_para,
            fail_silently=True
        )
        print(f"Correo de NUEVA solicitud enviado a {solicitante.email}") 

    except Exception as e:
        print(f"Error al enviar correo de nueva solicitud: {e}")

def enviar_notificacion_cambio_estado(solicitud, nuevo_estado_nombre):
    try:
        solicitante = solicitud.solicitante
        titulo_solicitud = solicitud.sca_titulo

        asunto = f"Actualización de tu Solicitud: #{solicitud.sca_id} - {titulo_solicitud}"

        mensaje = f"""
        Estimado(a) {solicitante.first_name},

        Le informamos que su solicitud "{titulo_solicitud}" ha cambiado su estado a: "{nuevo_estado_nombre}".

        Puede revisar los detalles de su solicitud en la plataforma.

        Atentamente,
        El Equipo de TECHO TI
        """

        email_desde = settings.EMAIL_HOST_USER
        email_para = ['jorg.fuentesc@duocuc.cl']#[solicitante.email]

        send_mail(
            asunto,
            mensaje,
            email_desde,
            email_para,
            fail_silently=True
        )
        print(f"Correo de notificación enviado a {solicitante.email}")

    except Exception as e:
        print(f"Error al enviar correo en segundo plano: {e}")
        
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_tipo_usuario(request):
    try:
        nombre = request.data.get('tiu_nombre')
        if not nombre:
            return Response(
                {"error": "El campo 'tiu_nombre' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if TipoUsuario.objects.filter(tiu_nombre=nombre).exists():
            return Response(
                {"error": f"El tipo de usuario '{nombre}' ya existe."},
                status=status.HTTP_400_BAD_REQUEST
            )

        nuevo_tipo = TipoUsuario.objects.create(tiu_nombre=nombre)

        response_data = {
            "mensaje": "Tipo de usuario creado correctamente.",
            "tipo_usuario": {
                "tiu_id": nuevo_tipo.tiu_id,
                "tiu_nombre": nuevo_tipo.tiu_nombre
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ver_tipos_usuario(request):

    try:
        tipos_usuario = TipoUsuario.objects.filter(tiu_vigencia=True)
        results = []
        for tipo in tipos_usuario:
            results.append({
                "tiu_id": tipo.tiu_id,
                "tiu_nombre": tipo.tiu_nombre,
                "tiu_fecha_creacion": tipo.tiu_fecha_creacion
            })
        
        return Response(results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al obtener los tipos de usuario.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asignar_tipo_usuario(request):
    try:
        rut_usuario = request.data.get('rut')
        tipo_id = request.data.get('tiu_id')

        if not rut_usuario or not tipo_id:
            return Response(
                {"error": "Los campos 'rut' y 'tiu_id' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            usuario_a_modificar = CustomUser.objects.get(rut=rut_usuario)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": f"No se encontró ningún usuario con el RUT: {rut_usuario}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            nuevo_tipo = TipoUsuario.objects.get(tiu_id=tipo_id)
        except TipoUsuario.DoesNotExist:
            return Response(
                {"error": f"No se encontró ningún tipo de usuario con el ID: {tipo_id}"},
                status=status.HTTP_404_NOT_FOUND
            )

        usuario_a_modificar.tiu_id = nuevo_tipo
        usuario_a_modificar.save(update_fields=['tiu_id'])

        response_data = {
            "mensaje": "Tipo de usuario asignado correctamente.",
            "usuario": {
                "rut": usuario_a_modificar.rut,
                "email": usuario_a_modificar.email,
                'id_tipo': nuevo_tipo.tiu_id,
                "tipo_asignado": nuevo_tipo.tiu_nombre
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al asignar el tipo de usuario.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_usuarios(request):
        
    try:
        id_filtro = request.query_params.get('id', None)
        rut_filtro = request.query_params.get('rut', None)

        queryset = CustomUser.objects.select_related('tiu_id')
        error_msg = ""

        if id_filtro:
            queryset = queryset.filter(id=id_filtro)
            error_msg = f"No se encontró ningún usuario con el ID: {id_filtro}"
        
        elif rut_filtro:
            queryset = queryset.filter(rut=rut_filtro)
            error_msg = f"No se encontró ningún usuario con el RUT: {rut_filtro}"
        
        
        usuarios = queryset.order_by('id')
        
        if (id_filtro or rut_filtro) and not usuarios.exists():
            return Response({"error": error_msg}, status=status.HTTP_404_NOT_FOUND)

        results = []
        for usuario in usuarios:
            tipo_nombre = None
            if usuario.tiu_id:
                tipo_nombre = usuario.tiu_id.tiu_nombre

            results.append({
                "id": usuario.id,
                "email": usuario.email,
                "rut": usuario.rut,
                "nombre": usuario.first_name,
                "apellido_paterno": usuario.last_name,
                "apellido_materno": usuario.apellido_materno,
                "tipo_usuario": tipo_nombre,
                "es_staff": usuario.is_staff,
                "esta_activo": usuario.is_active
            })

        return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al listar los usuarios.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def anular_solicitud(request):    
    ESTADO_ANULADO_ID = 5 
    
    try:
        solicitud_id = request.data.get('solicitud_id')

        if not solicitud_id:
            return Response(
                {"error": "El campo 'solicitud_id' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            
            try:
                solicitud = SolicitudAyuda.objects.get(pk=solicitud_id)
            except SolicitudAyuda.DoesNotExist:
                return Response(
                    {"error": f"La solicitud con id {solicitud_id} no existe."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                estado_anulado = EstadoSolicitud.objects.get(pk=ESTADO_ANULADO_ID)
            except EstadoSolicitud.DoesNotExist:
                return Response(
                    {"error": f"Error de configuración: El estado 'Anulado' (ID {ESTADO_ANULADO_ID}) no existe en la base de datos."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if solicitud.est_id == estado_anulado:
                return Response(
                    {"mensaje": f"La solicitud {solicitud_id} ya se encontraba anulada."},
                    status=status.HTTP_200_OK
                )
            
            solicitud.est_id = estado_anulado
            solicitud.sca_usuario_actualizacion = request.user
            solicitud.save()

            observacion = f"Solicitud ANULADA por el usuario: {request.user.email}."
            BitacoraSolicitud.objects.create(
                sca_id=solicitud,
                usuario=request.user,
                bsca_observacion=observacion
            )

            response_data = {
                "mensaje": "Solicitud anulada correctamente.",
                "solicitud": {
                    "sca_id": solicitud.sca_id,
                    "sca_titulo": solicitud.sca_titulo,
                    "nuevo_estado": estado_anulado.est_nombre
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado al anular la solicitud.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def desactivar_usuario(request):        
    try:
        usuario_id = request.data.get('id')
        rut_usuario = request.data.get('rut')
        
        usuario_a_modificar = None

        if usuario_id:
            usuario_a_modificar = get_object_or_404(CustomUser, id=usuario_id)
            error_msg = f"No se encontró ningún usuario con el ID: {usuario_id}"
        elif rut_usuario:
            usuario_a_modificar = get_object_or_404(CustomUser, rut=rut_usuario)
            error_msg = f"No se encontró ningún usuario con el RUT: {rut_usuario}"
        else:
            return Response(
                {"error": "Debes proporcionar un 'id' o un 'rut' de usuario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not usuario_a_modificar.is_active:
             return Response(
                {"mensaje": "Este usuario ya se encontraba desactivado."},
                status=status.HTTP_200_OK
            )
            
        usuario_a_modificar.is_active = False
        usuario_a_modificar.save(update_fields=['is_active'])

        return Response(
            {"mensaje": "Usuario desactivado correctamente.", "usuario_email": usuario_a_modificar.email},
            status=status.HTTP_200_OK
        )

    except CustomUser.DoesNotExist:
         return Response({"error": error_msg}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activar_usuario(request):
        
    try:
        usuario_id = request.data.get('id')
        rut_usuario = request.data.get('rut')
        
        usuario_a_modificar = None
        error_msg = ""

        if usuario_id:
            usuario_a_modificar = get_object_or_404(CustomUser, id=usuario_id)
            error_msg = f"No se encontró ningún usuario con el ID: {usuario_id}"
        elif rut_usuario:
            usuario_a_modificar = get_object_or_404(CustomUser, rut=rut_usuario)
            error_msg = f"No se encontró ningún usuario con el RUT: {rut_usuario}"
        else:
            return Response(
                {"error": "Debes proporcionar un 'id' o un 'rut' de usuario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if usuario_a_modificar.is_active:
             return Response(
                {"mensaje": "Este usuario ya se encontraba activo."},
                status=status.HTTP_200_OK
            )
            
        usuario_a_modificar.is_active = True
        usuario_a_modificar.save(update_fields=['is_active'])

        return Response(
            {"mensaje": "Usuario activado correctamente.", "usuario_email": usuario_a_modificar.email},
            status=status.HTTP_200_OK
        )

    except CustomUser.DoesNotExist:
         return Response({"error": error_msg}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {"error": "Ocurrió un error inesperado.", "detalle": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )