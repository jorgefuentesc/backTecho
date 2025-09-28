# solicitudes/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from .models import SolicitudAyuda, DocumentoSolicitud, BitacoraSolicitud, EstadoSolicitud

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
        
        # --- 2. Construcción Manual de la Respuesta JSON ---
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
                "sca_titulo": solicitud.sca_titulo,
                "estado": solicitud.est_id.est_nombre,
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