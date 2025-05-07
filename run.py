<<<<<<< HEAD
from flask import Flask, render_template, jsonify
from crear_puntos import crear_puntos_bp
from crear_puntos_curva import crear_puntos_curva_bp
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.register_blueprint(crear_puntos_bp)
app.register_blueprint(crear_puntos_curva_bp)
=======
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import subprocess
import multiprocessing
from crear_puntos import crear_puntos_bp
from crear_puntos_curva import crear_puntos_curva_bp
from seleccionar_objetos import seleccionar_objetos_directo_bp
from perfiles import perfiles_bp
from etiquetado import etiquetado_bp
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil
from obtener_objetos import obtener_objetos_bp
from cargar_dwg import abrir_dwg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
>>>>>>> 3a25e43 (fix update)

@app.route('/recibir_datos_civil3d', methods=['POST'])
def recibir_datos_civil3d():
    try:
        data = request.get_json()
        logger.info("Datos recibidos desde Civil 3D:")
        logger.info(data)
        return jsonify({'message': 'Datos recibidos y procesados correctamente'}), 200
    except Exception as e:
        logger.error(f"Error al recibir o procesar datos de Civil 3D: {e}")
        return jsonify({'error': f'Error al recibir o procesar datos: {e}'}), 400

@app.route('/listar_scripts')
def listar_scripts():
    try:
        scripts = [f for f in os.listdir('.') if f.endswith('.py') and f not in ['run.py', '__init__.py']]
        return jsonify(scripts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    multiprocessing.freeze_support()

    try:
        logger.info("Registrando los blueprints...")
        app.register_blueprint(crear_puntos_bp)
        app.register_blueprint(crear_puntos_curva_bp)
        app.register_blueprint(seleccionar_objetos_directo_bp)
        app.register_blueprint(perfiles_bp)
        app.register_blueprint(etiquetado_bp)
        app.register_blueprint(obtener_objetos_bp)
        logger.info("Blueprints registrados correctamente.")
    except Exception as e:
        logger.error(f"Error al registrar los blueprints: {e}")
        raise SystemExit(f"Fallo al registrar los blueprints: {e}")

    @app.route('/cargar_datos', methods=['POST'])
    def cargar_datos():
        try:
            data = request.get_json()
            coordenadas_data = data.get('coordenadas')
            tuberias_data = data.get('tuberias')
            logger.info("Datos de coordenadas recibidos del formulario:")
            logger.info(coordenadas_data)
            logger.info("Datos de tuberías recibidos del formulario:")
            logger.info(tuberias_data)
            return jsonify({'message': 'Datos cargados y procesados correctamente desde el formulario'}), 200
        except Exception as e:
            logger.error(f"Error al cargar o procesar los datos del formulario: {e}")
            return jsonify({'error': f'Error al cargar o procesar los datos del formulario: {e}'}), 500


    @app.route('/obtener_perfiles', methods=['GET'])
    def obtener_perfiles():
        try:
            logger.info("Intentando obtener perfiles de AutoCAD/Civil 3D (vía COM)...")
            acad = conectar_con_autocad_civil()
            if acad:
    
                perfiles = []
                desconectar_autocad_civil(acad)
                return jsonify(perfiles)
            else:
                return jsonify({"error": "No se pudo conectar con AutoCAD/Civil 3D"}), 500
        except Exception as e:
            logger.error(f"Error al obtener los perfiles de AutoCAD/Civil 3D (vía COM): {e}")
            return jsonify({"error": f"Error al obtener los perfiles de AutoCAD/Civil 3D (vía COM): {e}"}), 500

    # Ruta para abrir un archivo DWG
    @app.route('/abrir_dwg', methods=['POST'])
    def abrir_dwg_route():
        print("Entrando a la función abrir_dwg_route")
        logger.info("Recibida solicitud POST para /abrir_dwg")
        archivo_dwg = request.files.get('archivo_dwg')
        print(f"Archivo DWG recibido: {archivo_dwg}")

        if not archivo_dwg:
            print("Error: No se proporcionó el archivo DWG")
            return jsonify({"error": "No se proporcionó el archivo DWG"}), 400

        if not archivo_dwg.filename or not archivo_dwg.filename.lower().endswith('.dwg'):
            print("Error: El archivo subido no tiene la extensión .dwg")
            return jsonify({"error": "Por favor, sube un archivo con extensión .dwg"}), 400

        if not os.path.exists('uploads'):
            os.makedirs('uploads')
            print("Directorio 'uploads' creado.")

        archivo_guardado = os.path.join('uploads', archivo_dwg.filename)
        print(f"Ruta del archivo a guardar: {archivo_guardado}")
        try:
            archivo_dwg.save(archivo_guardado)
            print(f"Archivo guardado exitosamente en: {archivo_guardado}")
        except Exception as e_guardar:
            print(f"Error al guardar el archivo: {e_guardar}")
            return jsonify({"error": f"Error al guardar el archivo subido: {e_guardar}"}), 500

        print(f"Llamando a la función abrir_dwg con ruta: {archivo_guardado}")
        resultado = abrir_dwg(archivo_guardado)
        print(f"Resultado de abrir_dwg: {resultado}")

        try:
            os.remove(archivo_guardado)
            print(f"Archivo temporal eliminado: {archivo_guardado}")
        except Exception as e_eliminar:
            print(f"Error al eliminar el archivo temporal: {e_eliminar}")

        if "error" in resultado:
            return jsonify(resultado), 500
        else:
            return jsonify(resultado), 200

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/csv_editor')
    def csv_editor():
        return render_template('csv_editor.html')

    @app.route('/listar_scripts')
    def listar_scripts():
        try:
            logger.info("Listando los scripts en el directorio...")
            scripts = [f for f in os.listdir('.') if f.endswith('.py') and f not in ['run.py', '__init__.py', 'autocad_civil.py']]
            logger.info(f"Scripts encontrados: {scripts}")
            return jsonify(scripts)
        except Exception as e:
            logger.error(f"Error al listar los scripts: {e}")
            return jsonify({'error': f"Error al listar los scripts: {e}"}), 500

    @app.route('/ejecutar_script/<script_nombre>', methods=['POST'])
    def ejecutar_script(script_nombre):
        try:
            logger.info(f"Intentando ejecutar el script: {script_nombre}")

            if '..' in script_nombre or script_nombre.startswith('/'):
                logger.warning(f"Nombre de script peligroso o inválido: {script_nombre}")
                return jsonify({'error': 'Nombre de script no válido.'}), 400

            script_path = f'./{script_nombre}'
            logger.info(f"Ruta del script: {script_path}")

            if not os.path.exists(script_path):
                logger.error(f"El script '{script_nombre}' no se encuentra.")
                return jsonify({'error': f"El script '{script_nombre}' no se encuentra."}), 404

            logger.info(f"Ejecutando el script '{script_nombre}'...")
            result = subprocess.run(['python', script_path], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"El script '{script_nombre}.py' se ejecutó correctamente.")
                return jsonify({'message': f"El script '{script_nombre}' se ejecutó correctamente."})
            else:
                logger.error(f"Error al ejecutar el script '{script_nombre}': {result.stderr}")
                return jsonify({'error': f"Error al ejecutar el script '{script_nombre}': {result.stderr}"}), 500

        except Exception as e:
            logger.error(f"Ocurrió un error inesperado: {str(e)}")
            return jsonify({'error': f"Ocurrió un error inesperado: {str(e)}"}), 500

    try:
        logger.info("Iniciando la aplicación Flask...")
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación Flask: {e}")
        raise SystemExit(f"Fallo al iniciar la aplicación Flask: {e}")