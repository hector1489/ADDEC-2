import logging
from flask import Blueprint, jsonify, request
from pyautocad import Autocad, APoint
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

etiquetado_bp = Blueprint('etiquetado', __name__)

def obtener_objeto_acad(acad, identificador, tipo_objeto):
    """Función utilitaria para obtener objetos en AutoCAD."""
    try:
        if not acad:
            return None, "No hay conexión con AutoCAD."

        objeto = acad.doc.GetObject(identificador)
        if not objeto:
            return None, f"{tipo_objeto} no encontrado"

        logger.info(f"{tipo_objeto} con identificador {identificador} encontrado.")
        return objeto, None
    except Exception as e:
        logger.error(f"Error al obtener {tipo_objeto} con identificador {identificador}: {e}")
        return None, str(e)

def etiquetar_vertices(puntos, tipo="vertical", offset=5):
    """Función común para etiquetar puntos, ya sea verticales u horizontales."""
    etiquetas = []
    distancia_acumulada = 0
    for i, punto in enumerate(puntos):
        if i > 0:
            distancia_acumulada += puntos[i].distance_to(puntos[i - 1])

        if tipo == "vertical":
            etiqueta = f"Elevación: {punto.z:.2f}, Distancia: {distancia_acumulada:.2f}"
            posicion = APoint(punto.x, punto.y, punto.z + offset)
        else:
            etiqueta = f"X: {punto.x:.2f}, Y: {punto.y:.2f}, Distancia: {distancia_acumulada:.2f}"
            posicion = APoint(punto.x, punto.y + offset, punto.z)

        etiquetas.append((etiqueta, posicion, 2.5))

    return etiquetas

@etiquetado_bp.route('/etiquetar_vertices_verticales', methods=['POST'])
def etiquetar_vertices_verticales():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        perfil_id = data.get('perfil_id')

        if not perfil_id:
            return jsonify({'error': 'Se requiere perfil_id'}), 400

        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        perfil, error = obtener_objeto_acad(acad, perfil_id, "Perfil")
        if error:
            return jsonify({'error': error}), 404

        if not hasattr(perfil, 'Coordinates'):
            return jsonify({'error': 'El perfil no tiene coordenadas válidas.'}), 400

        puntos = [APoint(p.x, p.y, p.z) for p in perfil.Coordinates]
        etiquetas = etiquetar_vertices(puntos, tipo="vertical")

        for etiqueta, posicion, altura in etiquetas:
            acad.model.AddText(etiqueta, posicion, altura)

        return jsonify({'message': 'Vértices verticales etiquetados correctamente', 'total_etiquetas': len(etiquetas)}), 200

    except Exception as e:
        logger.error(f"Error al etiquetar vértices verticales: {e}")
        return jsonify({'error': f'Error al etiquetar vértices verticales: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

@etiquetado_bp.route('/etiquetar_vertices_horizontales', methods=['POST'])
def etiquetar_vertices_horizontales():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        alineamiento_id = data.get('alineamiento_id')

        if not alineamiento_id:
            return jsonify({'error': 'Se requiere alineamiento_id'}), 400

        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        alineamiento, error = obtener_objeto_acad(acad, alineamiento_id, "Alineamiento")
        if error:
            return jsonify({'error': error}), 404

        if not hasattr(alineamiento, 'Coordinates'):
            return jsonify({'error': 'El alineamiento no tiene coordenadas válidas.'}), 400

        puntos = [APoint(p.x, p.y, p.z) for p in alineamiento.Coordinates]
        etiquetas = etiquetar_vertices(puntos, tipo="horizontal")

        for etiqueta, posicion, altura in etiquetas:
            acad.model.AddText(etiqueta, posicion, altura)

        return jsonify({'message': 'Vértices horizontales etiquetados correctamente', 'total_etiquetas': len(etiquetas)}), 200

    except Exception as e:
        logger.error(f"Error al etiquetar vértices horizontales: {e}")
        return jsonify({'error': f'Error al etiquetar vértices horizontales: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

@etiquetado_bp.route('/etiquetar_distancias', methods=['POST'])
def etiquetar_distancias():
    acad = None
    civil3d = None
    try:
        data = request.get_json()
        polilinea_id = data.get('polilinea_id')
        punto_referencia = data.get('punto_referencia')

        if not polilinea_id or not punto_referencia:
            return jsonify({'error': 'Se requieren polilinea_id y punto_referencia'}), 400

        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        polilinea, error = obtener_objeto_acad(acad, polilinea_id, "Polilínea")
        if error:
            return jsonify({'error': error}), 404

        if not hasattr(polilinea, 'Coordinates'):
            return jsonify({'error': 'La polilínea no tiene coordenadas válidas.'}), 400

        punto_ref = APoint(punto_referencia['x'], punto_referencia['y'], punto_referencia['z'])
        puntos = [APoint(p.x, p.y, p.z) for p in polilinea.Coordinates]

        etiquetas = []
        for punto in puntos:
            distancia = punto_ref.distance_to(punto)
            etiqueta = f"Distancia: {distancia:.2f}"
            etiquetas.append((etiqueta, APoint(punto.x, punto.y + 5, punto.z), 2.5))

        for etiqueta, posicion, altura in etiquetas:
            acad.model.AddText(etiqueta, posicion, altura)

        return jsonify({'message': 'Distancias etiquetadas correctamente', 'total_etiquetas': len(etiquetas)}), 200

    except Exception as e:
        logger.error(f"Error al etiquetar distancias: {e}")
        return jsonify({'error': f'Error al etiquetar distancias: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")