from flask import Blueprint, jsonify, request
import logging
from pyautocad import Autocad
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

seleccionar_objetos_directo_bp = Blueprint('seleccionar_objetos', __name__)
logger = logging.getLogger(__name__)

@seleccionar_objetos_directo_bp.route('/seleccionar_objetos', methods=['POST'])
def seleccionar_objetos():
    """
    Permite al usuario seleccionar objetos en AutoCAD/Civil 3D y devuelve sus ObjectIds.
    """
    acad = None
    civil3d = None
    try:
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()

        if not acad:
            return jsonify({"error": "No se pudo establecer conexión con AutoCAD/Civil 3D."}), 500

        try:
            seleccion = acad.get_selection()
            if seleccion:
                object_ids = [obj.ObjectId for obj in seleccion]
                return jsonify({'object_ids': object_ids}), 200
            else:
                return jsonify({'message': 'No se seleccionaron objetos.'}), 200
        except Exception as e:
            logger.error(f"Error al seleccionar objetos: {e}")
            return jsonify({'error': f'Error al seleccionar objetos: {e}'}), 500

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"error": "Error inesperado durante la ejecución"}), 500

    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

@seleccionar_objetos_directo_bp.route('/generar_polilinea', methods=['POST'])
def generar_polilinea():
    """
    Ruta para generar una polilínea 3D en Civil 3D a partir de ObjectIds seleccionados.
    """
    acad = None
    civil3d = None
    try:
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()

        if not acad:
            return jsonify({"error": "No se pudo establecer conexión con AutoCAD/Civil 3D."}), 500

        data = request.get_json()
        if not data:
            logging.error("No se proporcionaron datos JSON válidos.")
            return jsonify({'error': 'No se proporcionaron datos JSON válidos.'}), 400

        object_ids = data.get('object_ids')
        if not object_ids or not isinstance(object_ids, list):
            logging.error("El campo object_ids es obligatorio y debe ser una lista.")
            return jsonify({'error': 'El campo object_ids es obligatorio y debe ser una lista.'}), 400

        model = acad.model
        points = []

        for obj_id in object_ids:
            try:
                obj = acad.doc.GetObject(obj_id)
                if obj.ObjectName == 'AcDb3dPolyline' and hasattr(obj, 'Coordinates'):
                    coords = obj.Coordinates
                    if len(coords) % 3 == 0:
                        for i in range(0, len(coords), 3):
                            points.extend(coords[i:i+3])
                    else:
                        return jsonify({'error': f'Las coordenadas del objeto {obj_id} no son válidas para una polilínea 3D.'}), 400
            except Exception as e:
                logging.error(f"Error al obtener objeto {obj_id}: {e}")
                return jsonify({'error': f"Error al procesar el objeto {obj_id}: {str(e)}"}), 500

        if points:
            model.Add3DPoly(points)
            return jsonify({'message': 'Polilínea 3D generada correctamente.'}), 200
        else:
            return jsonify({'error': 'No se encontraron coordenadas válidas para la polilínea.'}), 400

    except Exception as e:
        logger.error(f"Error al generar polilínea: {e}")
        return jsonify({'error': f"Error interno: {e}"}), 500

    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")