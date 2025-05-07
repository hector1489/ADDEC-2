from flask import Blueprint, jsonify, request
from pyautocad import Autocad, APoint
import logging
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

perfiles_bp = Blueprint('perfiles', __name__)

def generar_perfil_terreno_acad(acad, alineamiento_id, polilinea_id):
    """Genera un perfil de terreno en AutoCAD."""
    try:
        if not acad:
            return {'error': 'No hay conexión con AutoCAD.'}

        alineamiento = acad.doc.GetObject(alineamiento_id)
        polilinea = acad.doc.GetObject(polilinea_id)

        if not alineamiento or not polilinea:
            return {'error': 'Alineamiento o polilínea no encontrados'}

        puntos_alineamiento = [APoint(p.x, p.y, p.z) for p in alineamiento.Coordinates]

        elevaciones = []
        for punto in puntos_alineamiento:
            elevacion = polilinea.GetHeightAtPoint(punto)
            elevaciones.append(elevacion)

        perfil = acad.model.AddPolyline3D([APoint(p.x, p.y, e) for p, e in zip(puntos_alineamiento, elevaciones)])

        return {'message': 'Perfil de terreno generado correctamente'}

    except Exception as e:
        logger.error(f"Error al generar perfil de terreno en AutoCAD: {e}")
        return {'error': f'Error al generar perfil de terreno en AutoCAD: {e}'}

def copiar_perfil_tapado_acad(acad, perfil_id, distancia_tapa):
    """Copia un perfil en AutoCAD con una distancia de tapa vertical."""
    try:
        if not acad:
            return {'error': 'No hay conexión con AutoCAD.'}

        perfil_original = acad.doc.GetObject(perfil_id)

        if not perfil_original:
            return {'error': 'Perfil original no encontrado'}

        puntos_original = [APoint(p.x, p.y, p.z) for p in perfil_original.Coordinates]

        puntos_tapado = [APoint(p.x, p.y, p.z + distancia_tapa) for p in puntos_original]

        perfil_tapado = acad.model.AddPolyline3D(puntos_tapado)

        return {'message': 'Perfil copiado con distancia tapada correctamente'}

    except Exception as e:
        logger.error(f"Error al copiar perfil con distancia tapada en AutoCAD: {e}")
        return {'error': f'Error al copiar perfil con distancia tapada en AutoCAD: {e}'}

def copiar_rasante_acad(acad, perfil_id):
    """Copia la línea de rasante de un perfil de terreno en AutoCAD."""
    try:
        if not acad:
            return {'error': 'No hay conexión con AutoCAD.'}

        perfil_terreno = acad.doc.GetObject(perfil_id)

        if not perfil_terreno:
            return {'error': 'Perfil de terreno no encontrado'}

        linea_rasante = perfil_terreno.GetGradeline()

        if not linea_rasante:
            return {'error': 'Línea de rasante no encontrada en el perfil'}

        puntos_rasante = [APoint(p.x, p.y, p.z) for p in linea_rasante.Coordinates]

        rasante_copiada = acad.model.AddPolyline3D(puntos_rasante)

        return {'message': 'Línea de rasante copiada correctamente'}

    except Exception as e:
        logger.error(f"Error al copiar línea de rasante en AutoCAD: {e}")
        return {'error': f'Error al copiar línea de rasante en AutoCAD: {e}'}

def minimizar_vertices_rasante_acad(acad, rasante_id, tolerancia):
    """Minimiza los vértices de una línea de rasante en AutoCAD."""
    try:
        if not acad:
            return {'error': 'No hay conexión con AutoCAD.'}

        linea_rasante = acad.doc.GetObject(rasante_id)

        if not linea_rasante:
            return {'error': 'Línea de rasante no encontrada'}

       
        logging.warning("La funcionalidad de minimizar vértices de rasante no está completamente implementada en este ejemplo.")
        return {'message': 'Vértices de línea de rasante minimizados correctamente (funcionalidad no implementada)'}

    except Exception as e:
        logger.error(f"Error al minimizar vértices de línea de rasante en AutoCAD: {e}")
        return {'error': f'Error al minimizar vértices de línea de rasante en AutoCAD: {e}'}

@perfiles_bp.route('/generar_perfil_terreno', methods=['POST'])
def generar_perfil_terreno():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        result = generar_perfil_terreno_acad(acad, data.get('alineamiento_id'), data.get('polilinea_id'))
        return jsonify(result), 200 if 'error' not in result else 500

    except Exception as e:
        logger.error(f"Error al generar perfil de terreno: {e}")
        return jsonify({'error': f'Error al generar perfil de terreno: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

@perfiles_bp.route('/copiar_perfil_tapado', methods=['POST'])
def copiar_perfil_tapado():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        result = copiar_perfil_tapado_acad(acad, data.get('perfil_id'), data.get('distancia_tapa'))
        return jsonify(result), 200 if 'error' not in result else 500

    except Exception as e:
        logger.error(f"Error al copiar perfil con distancia tapada: {e}")
        return jsonify({'error': f'Error al copiar perfil con distancia tapada: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

@perfiles_bp.route('/copiar_rasante', methods=['POST'])
def copiar_rasante():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        result = copiar_rasante_acad(acad, data.get('perfil_id'))
        return jsonify(result), 200 if 'error' not in result else 500

    except Exception as e:
        logger.error(f"Error al copiar línea de rasante: {e}")
        return jsonify({'error': f'Error al copiar línea de rasante: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

@perfiles_bp.route('/minimizar_vertices_rasante', methods=['POST'])
def minimizar_vertices_rasante():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        result = minimizar_vertices_rasante_acad(acad, data.get('rasante_id'), data.get('tolerancia'))
        return jsonify(result), 200 if 'error' not in result else 500

    except Exception as e:
        logger.error(f"Error al minimizar vértices de línea de rasante: {e}")
        return jsonify({'error': f'Error al minimizar vértices de línea de rasante: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")