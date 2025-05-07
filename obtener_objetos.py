from flask import Flask, Blueprint, jsonify
import logging
from pyautocad import Autocad
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

obtener_objetos_bp = Blueprint('obtener_objetos', __name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@obtener_objetos_bp.route('/obtener_objetos', methods=['GET'])
def obtener_objetos():
    """Obtiene los IDs y la información de los objetos de AutoCAD/Civil 3D."""
    acad = None
    civil3d = None
    app_name = "AutoCAD"
    try:
        pythoncom.CoInitialize()
        logger.debug("🔧 Llamando a conectar_con_autocad_civil()...")
        acad, civil3d = conectar_con_autocad_civil()

        if not acad:
            logger.error("❌ No se pudo establecer conexión con AutoCAD/Civil 3D.")
            return jsonify({"error": "No se pudo establecer conexión con AutoCAD/Civil 3D."}), 500

        app_name = getattr(acad.Application, "Name", "AutoCAD")
        logger.info(f"Obteniendo objetos desde: {app_name}")
        logger.debug("🔍 Verificando si la aplicación AutoCAD/Civil 3D está activa...")
        doc = acad.ActiveDocument
        if doc is None:
            logger.warning("⚠️ No hay un documento activo en AutoCAD/Civil 3D.")
            return jsonify({"warning": "No hay un documento activo en AutoCAD/Civil 3D."}), 200
        else:
            logger.debug(f"📄 Documento activo: {doc.Name}")

        objetos_info = []

        try:
            logger.debug("🔎 Intentando acceder al espacio modelo desde el documento activo...")
            if hasattr(doc, "ModelSpace"):
                ms = doc.ModelSpace
                num_objetos = len(ms)
                logger.info(f"✨ Se encontraron {num_objetos} objetos en el espacio modelo.")
                if num_objetos > 0:
                    for i, obj in enumerate(ms):
                        try:
                            logger.debug(f"  ➡️ Procesando objeto {i+1} (Tipo: {obj.ObjectName})...")
                            handle = getattr(obj, "Handle", "N/A")
                            object_name = getattr(obj, "ObjectName", "N/A")
                            objeto_info = {
                                "Handle": handle,
                                "ObjectName": object_name,
                            }
                            objetos_info.append(objeto_info)
                            logger.debug(f"    ✅ Objeto {i+1}: Handle='{handle}', ObjectName='{object_name}'")
                        except Exception as obj_error:
                            logger.error(f"  ⚠️ Error al acceder a las propiedades del objeto {i+1} (Tipo: {getattr(obj, 'ObjectName', 'Desconocido')}): {obj_error}")
                            # Considerar añadir información básica del objeto problemático al JSON si es crítico
                            # objetos_info.append({"Handle": getattr(obj, "Handle", "ERROR"), "ObjectName": "ERROR - Problema al leer"})
                            continue # Saltar al siguiente objeto en caso de error
                else:
                    logger.info("📭 El espacio modelo está vacío.")
                    return jsonify({"warning": f"El espacio modelo de {app_name} está vacío."}), 200
            else:
                logger.warning("⚠️ No se pudo acceder a la propiedad 'ModelSpace' del documento.")
                return jsonify({"warning": f"No se pudo acceder al espacio modelo del documento {doc.Name}."}, 500)

        except Exception as e:
            logger.error(f"❌ No se pudo acceder al espacio modelo del documento: {e}")
            return jsonify({"error": f"No se pudo acceder al espacio modelo del documento {doc.Name}"}), 500

        if not objetos_info:
            logger.warning("📭 No se encontraron objetos en el espacio modelo.")
            return jsonify({"warning": f"No se encontraron objetos en {app_name}."}), 200

        logger.info(f"✅ Se obtuvieron {len(objetos_info)} objetos.")
        return jsonify(objetos_info), 200

    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return jsonify({"error": "Error inesperado durante la ejecución"}), 500

    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.debug("🧹 Recursos COM liberados.")
        except Exception as e:
            logger.error(f"⚠️ Error al liberar recursos COM: {e}")


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    app = Flask(__name__)
    app.register_blueprint(obtener_objetos_bp)

    with app.app_context():
        from flask import Response
        response = obtener_objetos()
        if isinstance(response, tuple):
            response, status_code = response
        print("\n✅ Resultado JSON:")
        print(response.get_data(as_text=True))