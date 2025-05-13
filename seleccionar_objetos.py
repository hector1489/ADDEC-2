from flask import Blueprint, jsonify
import logging
import pythoncom
from pyautocad import Autocad
import traceback
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

# Configuración del logger
logger = logging.getLogger("seleccionar_objetos")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(ch)

# Creación del Blueprint
seleccionar_objetos_pyacad_bp = Blueprint('seleccionar_objetos_pyacad', __name__)

def obtener_doc_acad():
    """Obtiene el documento activo de AutoCAD. Maneja la conexión y errores."""
    try:
        acad = Autocad()
        doc = acad.ActiveDocument
        if not doc:
            raise ValueError("No se ha podido obtener un documento activo en AutoCAD.")
        return doc
    except Exception as e:
        logger.error(f"❌ Error al conectar o obtener documento de AutoCAD: {str(e)}")
        return None

def obtener_selection_set(doc, nombre_set="TempSelection"):
    """Obtiene o crea un conjunto de selección temporal."""
    try:
        if nombre_set in doc.SelectionSets:
            selection_set = doc.SelectionSets.Item(nombre_set)
            logger.debug(f"✅ Conjunto de selección '{nombre_set}' encontrado.")
        else:
            selection_set = doc.SelectionSets.Add(nombre_set)
            logger.debug(f"✅ No había selección activa, creando conjunto de selección '{nombre_set}'.")
        return selection_set
    except Exception as e:
        logger.error(f"❌ Error al obtener o crear el conjunto de selección '{nombre_set}': {str(e)}")
        raise

@seleccionar_objetos_pyacad_bp.route('/seleccionar_objetos', methods=['POST'])
def seleccionar_objetos_pyacad():
    pythoncom.CoInitialize()
    try:
        logger.debug("🟡 Intentando conectar con AutoCAD...")

        doc = obtener_doc_acad()
        if not doc:
            return jsonify({"error": "No se pudo obtener el documento activo en AutoCAD."}), 500

        logger.debug("🟢 Conectado con AutoCAD.")
        
        # Intentar obtener o crear el conjunto de selección temporal
        selection_set = obtener_selection_set(doc)

        # Verificar si hay objetos seleccionados en el conjunto temporal
        if len(selection_set) == 0:
            logger.warning("⚠️ No hay objetos seleccionados en el conjunto 'TempSelection'.")
            return jsonify({"message": "No hay objetos seleccionados actualmente."}), 200

        # Extraer los IDs de los objetos seleccionados
        try:
            ids = [obj.ObjectID for obj in selection_set]
            logger.info(f"✅ Se encontraron {len(ids)} objetos en el conjunto 'TempSelection'.")
        except Exception as e:
            logger.error(f"❌ Error al extraer IDs de los objetos seleccionados: {str(e)}")
            return jsonify({"error": "Error al extraer los identificadores de los objetos seleccionados."}), 500

        # Devuelve los identificadores de los objetos seleccionados
        return jsonify({"object_ids": ids}), 200

    except Exception as e:
        logger.error("❌ Error general al intentar seleccionar objetos:")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        pythoncom.CoUninitialize()
        logger.info("🔚 Recursos COM liberados.")



# Ruta para generar una polilínea 3D a partir de la selección (se mantiene igual)
@seleccionar_objetos_pyacad_bp.route('/generar_polilinea_seleccionada', methods=['POST'])
def generar_polilinea_seleccionada():
    """Genera una polilínea 3D a partir de los objetos actualmente seleccionados."""
    acad = None
    civil3d = None
    pythoncom.CoInitialize()
    try:
        logger.debug("🟡 Conectando con AutoCAD y Civil 3D...")
        acad, civil3d = conectar_con_autocad_civil()

        if not acad:
            logger.error("❌ No se pudo establecer conexión con AutoCAD/Civil 3D.")
            return jsonify({"error": "No se pudo establecer conexión con AutoCAD/Civil 3D."}), 500

        doc = acad.ActiveDocument
        selection_set = None
        try:
            if "TempSelection" in doc.SelectionSets:
                selection_set = doc.SelectionSets.Item("TempSelection")
                logger.debug("✅ Conjunto de selección 'TempSelection' encontrado para generar polilínea.")
            else:
                logger.warning("⚠️ No se encontró un conjunto de selección activo para generar la polilínea.")
                return jsonify({'message': 'No hay objetos seleccionados para generar la polilínea.'}), 200

            # Verificar si hay objetos seleccionados
            if len(selection_set) == 0:
                logger.warning("⚠️ No hay objetos seleccionados para generar la polilínea.")
                return jsonify({'message': 'No hay objetos seleccionados para generar la polilínea.'}), 200

            points = []
            for obj in selection_set:
                try:
                    if obj.ObjectName == 'AcDb3dPolyline' and hasattr(obj, 'Coordinates'):
                        coords = obj.Coordinates
                        if len(coords) % 3 == 0:
                            for i in range(0, len(coords), 3):
                                points.extend(coords[i:i+3])
                        else:
                            logger.error(f"❌ Las coordenadas del objeto {obj.ObjectId} no son válidas para una polilínea 3D.")
                            continue
                    else:
                        logger.warning(f"⚠️ El objeto {obj.ObjectId} no es una polilínea 3D válida.")
                except Exception as e:
                    logger.error(f"❌ Error al procesar objeto {obj.ObjectId}: {e}")
                    continue

            if points:
                model = acad.model
                model.Add3DPoly(points)
                logger.info("✅ Polilínea 3D generada a partir de la selección.")
                return jsonify({'message': 'Polilínea 3D generada a partir de la selección.'}), 200
            else:
                logger.warning("⚠️ No se encontraron polilíneas 3D válidas en la selección.")
                return jsonify({'error': 'No se encontraron polilíneas 3D válidas en la selección.'}), 200

        except Exception as e:
            logger.error("❌ Error al generar polilínea desde la selección:")
            logger.error(traceback.format_exc())
            return jsonify({'error': f"Error interno: {e}"}), 500

    except Exception as e:
        logger.error("❌ Error general al intentar generar la polilínea:")
        logger.error(traceback.format_exc())
        return jsonify({'error': f"Error interno: {e}"}), 500

    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("🔚 Recursos COM liberados (generar_polilinea_seleccionada).")
        except Exception as e:
            logger.error(f"⚠️ Error al liberar recursos COM (generar_polilínea_seleccionada): {e}")



            