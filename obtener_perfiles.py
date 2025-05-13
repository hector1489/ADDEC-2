import logging
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil
from flask import jsonify

# Configuración del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def obtener_perfiles_autocad():
    """Obtiene perfiles de Civil 3D si está disponible."""
    acad = None
    civil3d = None
    try:
        pythoncom.CoInitialize()
        logger.debug("🔧 Iniciando conexión con AutoCAD/Civil 3D...")
        acad, civil3d = conectar_con_autocad_civil()

        if acad is None:
            logger.error("❌ No se pudo conectar con AutoCAD.")
            return {"error": "No se pudo conectar con AutoCAD."}

        if civil3d is None:
            logger.warning("⚠️ Conexión establecida solo con AutoCAD. No se pueden obtener perfiles de Civil 3D.")
            return {"warning": "Civil 3D no está disponible o no se pudo conectar."}

        logger.debug("✅ Conexión con Civil 3D exitosa. Obteniendo perfiles...")
        perfiles_info = obtener_perfiles_desde_civil3d(civil3d)

        if not perfiles_info:
            logger.info("📭 No se encontraron perfiles en el dibujo actual.")
            return {"warning": "No se encontraron perfiles en el dibujo."}

        logger.info(f"✅ Se encontraron {len(perfiles_info)} perfiles.")
        return perfiles_info

    except Exception as e:
        logger.exception("❌ Ocurrió un error inesperado.")
        return {"error": f"Error inesperado: {e}"}

    finally:
        try:
            logger.debug("🔧 Liberando recursos COM y desconectando AutoCAD/Civil 3D...")
            desconectar_autocad_civil(acad, civil3d)
            pythoncom.CoUninitialize()
            logger.info("🔁 COM liberado correctamente.")
        except Exception as e:
            logger.error(f"⚠️ Error al liberar recursos COM: {e}")


def obtener_perfiles_desde_civil3d(civil3d_app):
    """Obtiene perfiles de alineaciones desde la API COM de Civil 3D."""
    perfiles = []
    try:
        civil_doc = civil3d_app.ActiveDocument
        alignments = civil_doc.AlignmentsSiteless

        for alignment in alignments:
            for perfil in alignment.Profiles:
                perfiles.append({
                    "Alineación": alignment.Name,
                    "Perfil": perfil.Name,
                    "Tipo": str(perfil.Type),
                    "Estilo": perfil.StyleName,
                })

    except Exception as e:
        logger.exception("Error al obtener perfiles desde Civil 3D.")
        return []

    return perfiles


def obtener_xdata(obj):
    """Obtiene todas las XData del objeto."""
    try:
        if hasattr(obj, "XData"):
            return obj.XData
        else:
            return None
    except AttributeError as e:
        logger.error(f"Error al acceder a XData: {e}")
        return None


def obtener_alineacion(obj):
    """Intenta obtener información de alineación asociada al objeto."""
    try:
        if hasattr(obj, "XData"):
            xdata = obj.XData
            for data in xdata:
                if "Alineación" in data:
                    return data["Alineación"]
        return None
    except Exception as e:
        logger.error(f"Error al obtener alineación: {e}")
        return None

def obtener_perfil(obj):
    """Intenta obtener información de perfil asociada al objeto."""
    try:
        if hasattr(obj, "XData"):
            xdata = obj.XData
            for data in xdata:
                if "Perfil" in data:
                    return data["Perfil"]
        return None
    except Exception as e:
        logger.error(f"Error al obtener perfil: {e}")
        return None

def obtener_superficie(obj):
    """Intenta obtener información de superficie asociada al objeto."""
    try:
        if hasattr(obj, "XData"):
            xdata = obj.XData
            for data in xdata:
                if "Superficie" in data:
                    return data["Superficie"]
        return None
    except Exception as e:
        logger.error(f"Error al obtener superficie: {e}")
        return None