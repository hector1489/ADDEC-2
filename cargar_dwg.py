import logging
import os
import time
from pyautocad import Autocad
import pythoncom
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
import win32com.client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def abrir_dwg(ruta_archivo):
    """Abre un archivo DWG y hace visible la interfaz de AutoCAD, intentando una nueva pestaña si está ocupado."""
    acad_app = None
    com_initialized = False
    try:
        pythoncom.CoInitialize()
        com_initialized = True
        logger.debug("COM inicializado.")
        print("COM inicializado.")
        try:
            logger.info("Intentando obtener la aplicación de AutoCAD...")
            print("Intentando obtener la aplicación de AutoCAD...")
            acad_app = win32com.client.Dispatch("AutoCAD.Application.25")
            logger.info("Aplicación de AutoCAD obtenida exitosamente.")
            print("Aplicación de AutoCAD obtenida exitosamente.")
        except Exception as e_conexion_app:
            logger.error(f"Error al conectar con la aplicación de AutoCAD (conexión básica): {e_conexion_app}")
            print(f"Error al conectar con AutoCAD: {e_conexion_app}")
            return {"error": f"Error al conectar con AutoCAD: {e_conexion_app}"}

        if acad_app:
            ruta_absoluta = os.path.abspath(ruta_archivo)
            logger.info(f"Ruta absoluta del archivo a abrir: '{ruta_absoluta}'")
            print(f"Ruta absoluta del archivo a abrir: '{ruta_absoluta}'")
            logger.debug(f"Nombre de la aplicación AutoCAD: {acad_app.Name if hasattr(acad_app, 'Name') else 'Nombre no disponible'}")
            print(f"Nombre de la aplicación AutoCAD: {acad_app.Name if hasattr(acad_app, 'Name') else 'Nombre no disponible'}")
            logger.debug(f"Versión de la aplicación AutoCAD: {acad_app.Version if hasattr(acad_app, 'Version') else 'Versión no disponible'}")
            print(f"Versión de la aplicación AutoCAD: {acad_app.Version if hasattr(acad_app, 'Version') else 'Versión no disponible'}")

            try:
                logger.info(f"Intentando abrir el archivo DWG: '{ruta_absoluta}'...")
                print(f"Intentando abrir el archivo DWG: '{ruta_absoluta}'...")
                documento = acad_app.Documents.Open(ruta_absoluta)
                logger.info(f"Archivo '{os.path.basename(ruta_archivo)}' abierto exitosamente.")
                print(f"Archivo '{os.path.basename(ruta_archivo)}' abierto exitosamente.")

                logger.info("Intentando hacer visible la aplicación de AutoCAD...")
                print("Intentando hacer visible la aplicación de AutoCAD...")
                acad_app.Visible = True
                logger.info("Aplicación de AutoCAD ahora visible.")
                print("Aplicación de AutoCAD ahora visible.")

                app_name = acad_app.Name if hasattr(acad_app, 'Name') else 'AutoCAD'
                doc_name = os.path.basename(ruta_archivo)
                return {"success": f"Archivo '{doc_name}' abierto y AutoCAD mostrado."}

            except Exception as e_abrir:
                logger.warning(f"Error al ABRIR el archivo '{ruta_absoluta}': {e_abrir}")
                print(f"Error al ABRIR el archivo '{ruta_absoluta}': {e_abrir}")
                try:
                    logger.info("Intentando abrir el archivo en una nueva pestaña...")
                    print("Intentando abrir el archivo en una nueva pestaña...")
                    acad_app.Documents.Add(True) # True para que sea visible inmediatamente
                    nuevo_documento = acad_app.ActiveDocument
                    nuevo_documento.Open(ruta_absoluta)
                    logger.info(f"Archivo '{os.path.basename(ruta_archivo)}' abierto en una nueva pestaña.")
                    print(f"Archivo '{os.path.basename(ruta_archivo)}' abierto en una nueva pestaña.")
                    acad_app.Visible = True
                    return {"success": f"Archivo '{os.path.basename(ruta_archivo)}' abierto en una nueva pestaña."}
                except Exception as e_nueva_pestaña:
                    logger.error(f"Error al abrir en una nueva pestaña: {e_nueva_pestaña}")
                    print(f"Error al abrir en una nueva pestaña: {e_nueva_pestaña}")
                    app_name = acad_app.Name if hasattr(acad_app, 'Name') else 'AutoCAD'
                    return {"error": f"Error al abrir el archivo '{os.path.basename(ruta_archivo)}' o en una nueva pestaña en {app_name}: {e_abrir}, {e_nueva_pestaña}"}
        else:
            logger.error("No se pudo obtener la instancia de la aplicación de AutoCAD.")
            print("No se pudo obtener la instancia de la aplicación de AutoCAD.")
            return {"error": "No se pudo obtener la instancia de AutoCAD."}

    except Exception as e:
        logger.error(f"Error INESPERADO al procesar el archivo '{ruta_archivo}': {e}")
        print(f"Error INESPERADO al procesar el archivo '{ruta_archivo}': {e}")
        return {"error": f"Error inesperado al procesar el archivo: {e}"}
    finally:
        if com_initialized:
            pythoncom.CoUninitialize()
            logger.debug("COM desinicializado.")
            print("COM desinicializado.")

app = Flask(__name__)

@app.route('/abrir_dwg', methods=['POST'])
def abrir_dwg_route():
    logger.info("Recibida solicitud POST para /abrir_dwg")
    print("Recibida solicitud POST para /abrir_dwg")
    archivo_dwg = request.files.get('archivo_dwg')
    logger.debug(f"Objeto request.files: {request.files}")
    print(f"Objeto request.files: {request.files}")
    logger.debug(f"Objeto archivo_dwg: {archivo_dwg}")
    print(f"Objeto archivo_dwg: {archivo_dwg}")

    if not archivo_dwg:
        logger.error("No se proporcionó el archivo DWG en la solicitud.")
        print("No se proporcionó el archivo DWG en la solicitud.")
        return jsonify({"error": "No se proporcionó el archivo DWG"}), 400

    if not archivo_dwg.filename or not archivo_dwg.filename.lower().endswith('.dwg'):
        logger.error("El archivo subido no tiene la extensión .dwg.")
        print("El archivo subido no tiene la extensión .dwg.")
        return jsonify({"error": "Por favor, sube un archivo con extensión .dwg"}), 400

    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        logger.info(f"El directorio '{uploads_dir}' no existe. Creándolo...")
        print(f"El directorio '{uploads_dir}' no existe. Creándolo...")
        os.makedirs(uploads_dir)
        logger.info(f"Directorio '{uploads_dir}' creado.")
        print(f"Directorio '{uploads_dir}' creado.")

    nombre_archivo = secure_filename(archivo_dwg.filename)
    archivo_guardado = os.path.join(uploads_dir, nombre_archivo)
    logger.info(f"Ruta donde se intentará guardar el archivo subido: '{archivo_guardado}'")
    print(f"Ruta donde se intentará guardar el archivo subido: '{archivo_guardado}'")
    try:
        archivo_dwg.save(archivo_guardado)
        logger.info(f"Archivo subido y guardado exitosamente en: '{archivo_guardado}'")
        print(f"Archivo subido y guardado exitosamente en: '{archivo_guardado}'")
    except Exception as e_guardar:
        logger.error(f"Error al guardar el archivo subido en '{archivo_guardado}': {e_guardar}")
        print(f"Error al guardar el archivo subido en '{archivo_guardado}': {e_guardar}")
        return jsonify({"error": f"Error al guardar el archivo subido: {e_guardar}"}), 500

    logger.info(f"Llamando a la función abrir_dwg con la ruta: '{archivo_guardado}'")
    print(f"Llamando a la función abrir_dwg con la ruta: '{archivo_guardado}'")
    resultado = abrir_dwg(archivo_guardado)
    logger.debug(f"Resultado de la función abrir_dwg: {resultado}")
    print(f"Resultado de la función abrir_dwg: {resultado}")

    try:
        os.remove(archivo_guardado)
        logger.info(f"Archivo temporal eliminado: '{archivo_guardado}'")
        print(f"Archivo temporal eliminado: '{archivo_guardado}'")
    except Exception as e_eliminar:
        logger.warning(f"Error al eliminar el archivo temporal '{archivo_guardado}': {e_eliminar}")
        print(f"Error al eliminar el archivo temporal '{archivo_guardado}': {e_eliminar}")

    if "error" in resultado:
        logger.error(f"Error al abrir el archivo '{nombre_archivo}': {resultado['error']}")
        print(f"Error al abrir el archivo '{nombre_archivo}': {resultado['error']}")
        return jsonify(resultado), 500
    else:
        logger.info(f"Archivo '{nombre_archivo}' procesado y abierto exitosamente.")
        print(f"Archivo '{nombre_archivo}' procesado y abierto exitosamente.")
        return jsonify(resultado), 200

if __name__ == "__main__":
    print("Ejecutando cargar_dwg.py directamente...")
    ruta_del_dwg = "archivo_dwg.dwg"
    resultado_abrir = abrir_dwg(ruta_del_dwg)
    print("Resultado de intentar abrir directamente:", resultado_abrir)
    # app.run(debug=True)