import logging
import sys
import win32com.client
import pythoncom
from pyautocad import Autocad

# Configuración del logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


def conectar_con_autocad_civil(try_create=False):
    acad = None
    civil3d_app = None

    try:
        logger.debug("Inicializando COM con pythoncom.CoInitialize()...")
        print("DEBUG: Inicializando COM...")
        pythoncom.CoInitialize()
        logger.debug("COM inicializado.")
        print("DEBUG: COM inicializado.")

        # 1. Intentar conexión con AutoCAD 2025
        prog_id_autocad_2025 = "AutoCAD.Application.25"
        logger.debug(f"Intentando conexión con AutoCAD 2025 (GetObject) ProgID: '{prog_id_autocad_2025}'...")
        print(f"DEBUG: Intentando GetObject AutoCAD 2025 con ProgID: '{prog_id_autocad_2025}'...")
        try:
            acad = win32com.client.GetObject(None, prog_id_autocad_2025)
            version = getattr(acad.Application, "Version", "Desconocida")
            name = getattr(acad.Application, "Name", "Desconocido")
            logger.info(f"Conectado con AutoCAD 2025 (GetObject): {name} v{version}")
            print(f"INFO: Conectado con AutoCAD 2025 (GetObject): {name} v{version}")
        except Exception as e_getobject_acad:
            logger.warning(f"No se pudo conectar con AutoCAD 2025 (GetObject): {e_getobject_acad}")
            print(f"WARNING: Falló GetObject AutoCAD 2025: {e_getobject_acad}")
            acad = None

        # 2. Intentar conexión con Civil 3D 2025
        if acad is None:
            prog_id_civil_3d_2025 = "AeccXUiLand.AeccApplication.2025"
            logger.debug(f"Intentando conexión con Civil 3D 2025 (GetObject) ProgID: '{prog_id_civil_3d_2025}'...")
            print(f"DEBUG: Intentando GetObject Civil 3D 2025 con ProgID: '{prog_id_civil_3d_2025}'...")
            try:
                civil3d_app = win32com.client.GetObject(None, prog_id_civil_3d_2025)
                acad = civil3d_app.Application
                version = getattr(acad.Application, "Version", "Desconocida")
                name = getattr(acad.Application, "Name", "Desconocido")
                logger.info(f"Conectado con Civil 3D 2025 (GetObject): {name} v{version}")
                print(f"INFO: Conectado con Civil 3D 2025 (GetObject): {name} v{version}")
            except Exception as e_getobject_civil:
                logger.warning(f"No se pudo conectar con Civil 3D 2025 (GetObject): {e_getobject_civil}")
                print(f"WARNING: Falló GetObject Civil 3D 2025: {e_getobject_civil}")
                civil3d_app = None

        # 3. Intentar conexión con pyautocad si GetObject falló
        if acad is None:
            logger.debug("Intentando conectar con instancia de AutoCAD/Civil 3D (pyautocad)...")
            print("DEBUG: Intentando conectar con pyautocad (instancia existente)...")
            try:
                acad = Autocad(create_if_not_exists=False)
                logger.info(f"Conectado a instancia existente (pyautocad): {acad.doc.Application.Version}")
                print(f"INFO: Conectado a instancia existente (pyautocad): {acad.doc.Application.Version}")
                if "Civil 3D" in acad.doc.Application.Name:
                    try:
                        civil3d_app = win32com.client.Dispatch("AeccXUiLand.AeccApplication.2025")
                        logger.info("Civil 3D app (pyautocad) también conectado.")
                        print("INFO: Civil 3D app (pyautocad) también conectado.")
                    except Exception as e_civil_pyacad:
                        logger.warning(f"No se pudo obtener la app de Civil 3D desde pyautocad: {e_civil_pyacad}")
                        print(f"WARNING: Falló al obtener app Civil 3D desde pyautocad: {e_civil_pyacad}")
            except Exception as e_existing:
                logger.error(f"Error al conectar con AutoCAD/Civil 3D existente (pyautocad): {e_existing}")
                print(f"ERROR: Falló la conexión con pyautocad (existente): {e_existing}")
                acad = None
                if try_create:
                    logger.info("Intentando crear nueva instancia de AutoCAD (pyautocad)...")
                    print("INFO: Intentando crear nueva instancia de AutoCAD (pyautocad)...")
                    try:
                        acad = Autocad(create_if_not_exists=True)
                        logger.info(f"Nueva instancia creada (pyautocad): {acad.doc.Application.Version}")
                        print(f"INFO: Nueva instancia creada (pyautocad): {acad.doc.Application.Version}")
                        if "Civil 3D" in acad.doc.Application.Name:
                            try:
                                civil3d_app = win32com.client.Dispatch("AeccXUiLand.AeccApplication.2025")
                                logger.info("Civil 3D app (nueva instancia pyautocad) también conectado.")
                                print("INFO: Civil 3D app (nueva instancia pyautocad) también conectado.")
                            except Exception as e_civil_pyacad_new:
                                logger.warning(f"No se pudo obtener la app de Civil 3D desde la nueva instancia de pyautocad: {e_civil_pyacad_new}")
                                print(f"WARNING: Falló al obtener app Civil 3D desde nueva instancia pyautocad: {e_civil_pyacad_new}")
                    except Exception as e_create:
                        logger.error(f"Error al crear AutoCAD (pyautocad): {e_create}")
                        print(f"ERROR: Falló la creación de nueva instancia de pyautocad: {e_create}")
                        acad = None
                else:
                    logger.error("AutoCAD/Civil 3D no está abierto. Ejecuta la aplicación y vuelve a intentarlo.")
                    print("ERROR: AutoCAD/Civil 3D no está abierto. Ejecútalo y vuelve a intentar.")
                    return None, None

        return acad, civil3d_app

    except Exception as e_general:
        logger.error(f"Error general al conectar con AutoCAD/Civil 3D: {e_general}")
        print(f"ERROR GENERAL al conectar: {e_general}")
        return None, None

    finally:
        if not acad:
            logger.debug("Llamando a CoUninitialize() (no hubo conexión).")
            print("DEBUG: Llamando a CoUninitialize() (sin conexión).")
            try:
                pythoncom.CoUninitialize()
                logger.debug("COM liberado (CoUninitialize).")
                print("DEBUG: COM liberado (sin conexión).")
            except Exception as e_uninitialize:
                logger.error(f"Error al liberar COM (CoUninitialize): {e_uninitialize}")
                print(f"ERROR al liberar COM (sin conexión): {e_uninitialize}")


def desconectar_autocad_civil(acad=None, civil3d_app=None):
    try:
        logger.debug("Iniciando desconexión de AutoCAD y Civil 3D...")
        print("DEBUG: Iniciando desconexión...")

        if acad:
            try:
                version = getattr(acad, "Version", None)
                if not version and hasattr(acad, "Application"):
                    version = getattr(acad.Application, "Version", "Desconocida")
                logger.info(f"Desconectando AutoCAD versión: {version}")
                print(f"INFO: Desconectando AutoCAD versión: {version}")
                acad = None
            except Exception as e_acad_disconnect:
                logger.warning(f"Error al obtener versión/desconectar AutoCAD: {e_acad_disconnect}")
                print(f"WARNING: Error al desconectar AutoCAD: {e_acad_disconnect}")
        else:
            logger.info("ℹNo hay conexión activa a AutoCAD para cerrar.")
            print("INFO: No hay conexión activa para cerrar.")

        if civil3d_app:
            logger.info("Liberando referencia a Civil 3D.")
            print("INFO: Liberando referencia a Civil 3D.")
            civil3d_app = None

    except Exception as e_disconnect:
        logger.error(f"Error general al desconectar: {e_disconnect}")
        print(f"ERROR GENERAL al desconectar: {e_disconnect}")

    finally:
        try:
            pythoncom.CoUninitialize()
            logger.debug("COM liberado (CoUninitialize).")
            print("DEBUG: COM liberado (desconexión).")
        except Exception as e_uninitialize_finally:
            logger.error(f"Error al liberar COM en finally: {e_uninitialize_finally}")
            print(f"ERROR al liberar COM en finally (desconexión): {e_uninitialize_finally}")


# ** La llamada a la función a nivel superior .**
acad, civil3d_app = conectar_con_autocad_civil(try_create=True)

if acad:
    try:
        if civil3d_app:
            print("Civil 3D conectado (llamada principal)")
        else:
            print("AutoCAD conectado (llamada principal)")

        doc = acad.doc
        print(f"Nombre del documento activo: {doc.Name} (llamada principal)")

    except Exception as e:
        print(f"Ocurrió un error al interactuar con AutoCAD/Civil 3D (llamada principal): {e}")
    finally:
        desconectar_autocad_civil(acad, civil3d_app)
else:
    print("No se pudo establecer la conexión con AutoCAD/Civil 3D (llamada principal).")