import logging
from pyautocad import Autocad
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_perfiles_autocad():
    """Obtiene información detallada de los perfiles (polilíneas) de Civil 3D."""
    acad = None
    civil3d = None
    try:
        pythoncom.CoInitialize()
        # Conectar con AutoCAD y Civil 3D usando la función centralizada
        acad, civil3d = conectar_con_autocad_civil()

        if acad is None:
            return {"error": "No se pudo conectar con AutoCAD."}

        perfiles_info = []

        try:
            if hasattr(acad, "model_space") and acad.model_space:
                for obj in acad.model_space:
                    if obj.ObjectName == "AcDbPolyline":
                        try:
                            perfil_info = {
                                "Handle": obj.Handle,
                                "ObjectName": obj.ObjectName,
                                "Número de vértices": len(obj.vertices),
                                "Longitud": obj.Length,
                                "Vértices": list(obj.vertices),
                                "XData": obtener_xdata(obj),
                                "Layer": obj.Layer,
                                "Color": obj.TrueColor,
                                "Thickness": obj.Thickness,
                                "Alineación": obtener_alineacion(obj),
                                "Perfil": obtener_perfil(obj),
                                "Superficie": obtener_superficie(obj),
                            }
                            perfiles_info.append(perfil_info)
                        except Exception as obj_error:
                            logger.error(f"Error al procesar perfil (polyline) {obj.Handle}: {obj_error}")
                    # Aquí podrías agregar lógica adicional si civil3d está conectado
                    elif civil3d:
                        if obj.ObjectName.startswith("AeccDb"):
                            logger.info(f"Objeto de Civil 3D encontrado: {obj.ObjectName} - {obj.Handle}")
                            # Aquí podrías intentar acceder a propiedades específicas de objetos de Civil 3D
                            try:
                                if obj.ObjectName == "AeccDbAlignment":
                                    perfil_info_civil = {
                                        "Handle": obj.Handle,
                                        "ObjectName": obj.ObjectName,
                                        "Name": obj.Name,
                                        "Length": obj.Length,
                                        # Añade más propiedades relevantes de la alineación
                                    }
                                    perfiles_info.append(perfil_info_civil)
                                elif obj.ObjectName == "AeccDbProfile":
                                    perfil_info_civil = {
                                        "Handle": obj.Handle,
                                        "ObjectName": obj.ObjectName,
                                        "Name": obj.Name,
                                        "Length": obj.Length,
                                        # Añade más propiedades relevantes del perfil
                                    }
                                    perfiles_info.append(perfil_info_civil)
                                elif obj.ObjectName == "AeccDbSurface":
                                    perfil_info_civil = {
                                        "Handle": obj.Handle,
                                        "ObjectName": obj.ObjectName,
                                        "Name": obj.Name,
                                        # Añade más propiedades relevantes de la superficie
                                    }
                                    perfiles_info.append(perfil_info_civil)
                                else:
                                    logger.info(f"Objeto AeccDb no procesado: {obj.ObjectName}")
                            except Exception as civil_obj_error:
                                logger.error(f"Error al procesar objeto Civil 3D {obj.Handle} ({obj.ObjectName}): {civil_obj_error}")

            else:
                logger.warning("No hay objetos en el espacio modelo.")
                return {"warning": "No hay objetos en el espacio modelo."}

        except Exception as e:
            logger.error(f"Error al acceder al espacio modelo: {e}")
            return {"error": f"Error al acceder al espacio modelo: {e}"}

        if not perfiles_info:
            logger.warning("No se encontraron perfiles (polilíneas o objetos de Civil 3D relacionados) en AutoCAD.")
            return {"warning": "No se encontraron perfiles (polilíneas o objetos de Civil 3D relacionados) en AutoCAD."}

        return perfiles_info

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return {"error": f"Error inesperado: {e}"}

    finally:
        # Desconectar usando la función centralizada
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            logger.info("Recursos COM liberados.")
        except Exception as e:
            logger.error(f"Error al liberar recursos COM: {e}")

def obtener_xdata(obj):
    """Obtiene todas las XData del objeto."""
    try:
        if hasattr(obj, "XData"):
            return obj.XData
        else:
            return None
    except:
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