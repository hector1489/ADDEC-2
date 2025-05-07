import csv
import io
from flask import Blueprint, request, jsonify
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil
from win32com import client
from pyautocad import APoint

VARIANT = client.VARIANT
VT_ARRAY = 8192
VT_R8 = 5

import logging

logger = logging.getLogger(__name__)

crear_puntos_bp = Blueprint('crear_puntos', __name__)

def validar_coordenadas(coordenadas):
    """Valida las coordenadas de los puntos antes de ser procesadas."""
    errores = []
    for row in coordenadas:
        try:
            x, y, z = float(row['X']), float(row['Y']), float(row['Z'])
            id_punto = int(row['ID'])
            if id_punto < 0:
                errores.append(f"ID del punto debe ser positivo: {row}")
        except (ValueError, KeyError) as e:
            errores.append(f"Datos de coordenadas inválidos: {row}. Error: {e}")
    return errores

def validar_tuberias(tuberias):
    """Valida las tuberías antes de procesarlas."""
    errores = []
    for row in tuberias:
        try:
            pk_inicio = int(row['PK_INICIO'])
            pk_fin = int(row['PK_FIN'])
            if pk_inicio < 0 or pk_fin < 0:
                errores.append(f"Los PK deben ser positivos: {row}")
        except (ValueError, KeyError) as e:
            errores.append(f"Datos de tuberías inválidos: {row}. Error: {e}")
    return errores

def crear_puntos(acad, coordenadas):
    puntos = {}
    try:
        logging.debug("Entrando a la función crear_puntos")
        doc = acad.ActiveDocument
        logging.debug(f"Documento activo: {doc.Name if doc else None}")
        model_space = doc.ModelSpace
        logging.debug(f"Espacio modelo: {model_space if model_space else None}")

        try:
            logging.debug(f"  Tipo del espacio modelo: {type(model_space)}")
            logging.debug(f"  Nombre del espacio modelo (si existe): {model_space.Name}")
            logging.debug(f"  Cantidad de objetos en el espacio modelo: {model_space.Count}")
        except Exception as e:
            logging.warning(f"Error al inspeccionar el espacio modelo: {e}")

        if coordenadas:
            logging.debug(f"Número de coordenadas a procesar: {len(coordenadas)}")
            for row in coordenadas:
                try:
                    x = round(float(row['X']), 3)
                    y = round(float(row['Y']), 3)
                    z = round(float(row['Z']), 3)
                    descripcion = row.get('Etiqueta', 'Sin descripción')
                    id_punto = int(row['ID'])

                    logging.debug(f"Creando punto {id_punto} - X: {x}, Y: {y}, Z: {z}, Desc: {descripcion} (Redondeado)")
                    logging.debug(f"  ¿Documento activo válido? {acad.ActiveDocument is not None}")
                    logging.debug(f"  ¿Espacio modelo válido? {model_space is not None}")

                    point_array = (x, y, z)
                    safe_array = VARIANT(VT_ARRAY | VT_R8, point_array)

                    model_space.AddPoint(safe_array)
                    logging.debug(f"  Punto añadido al espacio modelo.")
                    puntos[id_punto] = (x, y, z)
                    logging.info(f"Punto {id_punto} agregado: {descripcion} en ({x}, {y}, {z})")
                except Exception as e:
                    logging.error(f"Error al crear punto {row.get('ID')}: {e}")
        else:
            logging.debug("No hay coordenadas para procesar.")
    except Exception as e:
        logging.error(f"Error al acceder al documento o al espacio modelo en crear_puntos: {e}")
    finally:
        logging.debug(f"Saliendo de la función crear_puntos. Puntos creados: {puntos.keys()}")
    return puntos

def crear_tuberias(acad, civil3d, tuberias, puntos):
    """Crea las tuberías en Civil 3D entre los puntos especificados"""
    logging.debug("Entrando a la función crear_tuberias")
    if not civil3d:
        logging.warning("Objeto civil3d es None. No se crearán tuberías.")
        logging.debug("Saliendo de la función crear_tuberias.")
        return

    logging.debug(f"Número de tuberías a procesar: {len(tuberias)}")
    for row in tuberias:
        try:
            pk_inicio = int(row['PK_INICIO'])
            pk_fin = int(row['PK_FIN'])
            id_tuberia = row['ID_TUBERIA']
            diametro = row['DIAMETRO']
            material = row['MATERIAL']
            presion_nominal = row['PRESION_NOMINAL']
            conexion_inicio = row['CONEXION_INICIO']
            conexion_fin = row['CONEXION_FIN']
            longitud = row['LONGITUD']
            pendiente = row['PENDIENTE']

            logging.debug(f"Creando tubería {id_tuberia} entre PK_INICIO: {pk_inicio} y PK_FIN: {pk_fin}")
            logging.debug(f"  Puntos disponibles: {puntos.keys()}")

            if pk_inicio not in puntos or pk_fin not in puntos:
                logging.warning(f"Puntos PK_INICIO ({pk_inicio}) o PK_FIN ({pk_fin}) no encontrados para tubería {id_tuberia}. Se omite la tubería.")
                continue

            start_point_coords = puntos[pk_inicio]
            end_point_coords = puntos[pk_fin]
            start_point = APoint(*start_point_coords)
            end_point = APoint(*end_point_coords)

            logging.debug(f"  Punto de inicio: {start_point}")
            logging.debug(f"  Punto de fin: {end_point}")

            if not isinstance(start_point, APoint) or not isinstance(end_point, APoint):
                logging.warning(f"Los puntos para la tubería {id_tuberia} no son válidos. Se omite la tubería.")
                continue

            pipe_network = civil3d.ActiveDocument.PipeNetworks.Add("Red de Tuberías")
            logging.debug(f"  Red de tuberías creada: {pipe_network.Name if pipe_network else None}")
            pipe = pipe_network.Pipes.AddByDiameter(start_point, end_point, diametro)
            logging.debug(f"  Tubería creada: {pipe if pipe else None}, Diámetro: {diametro}")
            if pipe is None:
                logging.warning(f"No se pudo crear la tubería {id_tuberia}.")
                continue

            descripcion_tuberia = (
                f"Tubería {id_tuberia}\n"
                f"Diámetro: {diametro}, Material: {material}\n"
                f"Presión Nominal: {presion_nominal}, Conexión: {conexion_inicio}-{conexion_fin}\n"
                f"Longitud: {longitud}, Pendiente: {pendiente}"
            )
            mid_point = APoint(
                (start_point.x + end_point.x) / 2,
                (start_point.y + end_point.y) / 2,
                (start_point.z + end_point.z) / 2
            )
            acad.model.AddText(descripcion_tuberia, mid_point, 3)
            logging.debug(f"Texto agregado a AutoCAD para la tubería.")

            logging.info(f"Tubería {id_tuberia} agregada entre puntos {pk_inicio} y {pk_fin}.")
        except Exception as e:
            logging.error(f"Error general al procesar la tubería {row.get('ID_TUBERIA')}: {e}")
    logging.debug("Saliendo de la función crear_tuberias.")

@crear_puntos_bp.route('/cargar_datos', methods=['POST'])
def cargar_datos():
    pythoncom.CoInitialize()
    acad = None
    civil3d = None
    puntos_creados = {}
    try:
        logging.info("Inicio de la ruta /cargar_datos")
        data = request.get_json(force=True)
        logging.debug(f"Datos recibidos: {data}")
        if not data:
            logging.error("No se proporcionaron datos JSON válidos.")
            return jsonify({'error': 'No se proporcionaron datos JSON válidos.'}), 400

        coordenadas = data.get('coordenadas')
        tuberias = data.get('tuberias', [])
        logging.debug(f"Coordenadas recibidas: {coordenadas is not None}")
        logging.debug(f"Tuberías recibidas: {tuberias is not None}")

        if not coordenadas or not isinstance(coordenadas, list):
            logging.error("Datos de coordenadas faltantes o en formato incorrecto.")
            return jsonify({'error': 'Datos de coordenadas faltantes o en formato incorrecto.'}), 400

        errores_coordenadas = validar_coordenadas(coordenadas)
        if errores_coordenadas:
            logging.error(f"Errores en los datos de coordenadas: {errores_coordenadas}")
            return jsonify({'error': 'Errores en las coordenadas', 'detalles': errores_coordenadas}), 400

        logging.debug("Intentando conectar con AutoCAD...")
        acad, civil3d = conectar_con_autocad_civil(try_create=True)
        logging.debug(f"Resultado de la conexión - acad: {acad}, civil3d: {civil3d}")
        if acad is None:
            return jsonify({'error': 'Error al conectar con AutoCAD.'}), 500

        # Crear los puntos
        puntos_creados = crear_puntos(acad, coordenadas)
        logging.debug(f"Puntos creados: {puntos_creados.keys()}")

        if civil3d and puntos_creados:
            logging.info("Intentando crear tuberías...")
            errores_tuberias = validar_tuberias(tuberias)
            if errores_tuberias:
                logging.warning(f"Errores en los datos de tuberías (se omitirán algunas tuberías): {errores_tuberias}")

            crear_tuberias(acad, civil3d, tuberias, puntos_creados)
            logging.info("Proceso de creación de puntos y (intento de) tuberías completado.")
            return jsonify({'message': 'Proceso completado. Puntos creados, se intentó crear tuberías (se omitieron datos faltantes).'}), 200
        elif acad and puntos_creados:
            logging.info("Proceso de creación de puntos completado (solo AutoCAD).")
            return jsonify({'message': 'Proceso de creación de puntos completado (solo AutoCAD).'}), 200
        else:
            return jsonify({'message': 'No se pudieron crear los puntos.'}), 500

    except pythoncom.com_error as com_err:
        logging.error(f"Error COM en cargar_datos: {com_err}")
        return jsonify({'error': f"Error COM: {com_err}"}), 500
    except Exception as e:
        logging.error(f"Error general en cargar_datos: {e}")
        return jsonify({'error': f"Error general: {e}"}), 500
    finally:
        logging.debug("Desconectando AutoCAD/Civil 3D y desinicializando COM.")
        desconectar_autocad_civil(acad, civil3d)
        pythoncom.CoUninitialize()