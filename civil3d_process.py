import multiprocessing
import queue
import pythoncom
from pyautocad import Autocad, ACAD, APoint
import logging
import win32com.client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def perform_civil3d_operation(acad, civil3d_app, command):
    """
    Realiza la operación de Civil 3D según el comando recibido.
    """
    try:
        if not isinstance(command, dict):
            raise ValueError("El comando debe ser un diccionario.")

        action = command.get('action', None)
        if action is None:
            raise ValueError("El comando debe contener una acción válida.")

        if action == 'crear_puntos':
            coordenadas = command.get('coordenadas', [])
            if not coordenadas:
                return {'error': 'No se proporcionaron datos de coordenadas.'}

            puntos_creados = {}
            model = acad.model
            for row in coordenadas:
                try:
                    x, y, z = float(row['X']), float(row['Y']), float(row['Z'])
                    descripcion = row.get('Etiqueta', 'Sin descripción')
                    id_punto = int(row['ID'])

                    logging.debug(f"Creando punto {id_punto} en ({x}, {y}, {z}) con descripción: {descripcion}")

                    point = APoint(x, y, z)
                    logging.debug(f"Punto APoint creado: {point}")
                    model.AddPoint(point)
                    logging.debug(f"Punto agregado a AutoCAD")
                    model.AddText(descripcion, APoint(x, y, z + 5), 2.5)
                    logging.debug(f"Texto agregado a AutoCAD")

                    puntos_creados[id_punto] = point
                    logging.info(f"Punto {id_punto} agregado: {descripcion} en ({x}, {y}, {z})")
                except Exception as e:
                    logging.error(f"Error al crear punto {row.get('ID')}: {e}")
            return {'message': f"{len(puntos_creados)} puntos creados.", 'puntos': puntos_creados}

        elif action == 'seleccionar_objetos':
            seleccion = acad.get_selection()
            if seleccion:
                object_ids = [obj.ObjectId for obj in seleccion]
                return {'object_ids': object_ids}
            else:
                return {'error': 'No se seleccionaron objetos.'}

        elif action == 'generar_polilinea':
            object_ids = command.get('object_ids', [])
            if not object_ids:
                return {'error': 'No se proporcionaron identificadores de objetos.'}

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
                            return {'error': 'Las coordenadas del objeto no son válidas para una polilínea 3D.'}
                except Exception as e:
                    logging.error(f"Error al obtener objeto {obj_id}: {e}")
                    return {'error': f"Error al procesar el objeto {obj_id}: {str(e)}"}

            if points:
                model.Add3DPoly(points)
                return {'message': 'Polilínea 3D generada correctamente.'}
            else:
                return {'error': 'No se encontraron coordenadas válidas para la polilínea.'}

        elif action == 'crear_tuberias' and civil3d_app:
            tuberias_data = command.get('tuberias', [])
            puntos_map = command.get('puntos', {})
            if not tuberias_data:
                return {'error': 'No se proporcionaron datos de tuberías.'}

            try:
                doc = civil3d_app.ActiveDocument
                pipe_network = doc.PipeNetworks.Add("Red desde Flask")
                tuberias_creadas = []
                for tuberia in tuberias_data:
                    pk_inicio = int(tuberia.get('PK_INICIO'))
                    pk_fin = int(tuberia.get('PK_FIN'))
                    diametro = float(tuberia.get('DIAMETRO'))
                    id_tuberia = tuberia.get('ID_TUBERIA')

                    start_point = puntos_map.get(pk_inicio)
                    end_point = puntos_map.get(pk_fin)

                    if not start_point or not end_point:
                        logging.warning(f"Puntos PK_INICIO {pk_inicio} o PK_FIN {pk_fin} no encontrados para tubería {id_tuberia}.")
                        continue

                    pipe = pipe_network.Pipes.AddByDiameter(start_point, end_point, diametro)
                    if pipe:
                        tuberias_creadas.append(id_tuberia)
                        logging.info(f"Tubería {id_tuberia} creada.")
                    else:
                        logging.warning(f"No se pudo crear la tubería {id_tuberia}.")
                return {'message': f"{len(tuberias_creadas)} tuberías creadas."}
            except Exception as e:
                logging.error(f"Error al crear tuberías en Civil 3D: {e}")
                return {'error': f'Error al crear tuberías: {e}'}

        else:
            return {'error': 'Acción no válida o Civil 3D no conectado para esta acción.'}

    except ValueError as ve:
        logging.warning(f"Error de validación: {ve}")
        return {'error': f'Error de validación: {ve}'}
    except Exception as e:
        logging.error(f"Error en Civil 3D: {e}")
        return {'error': f'Error en Civil 3D: {e}'}

def civil3d_process(command_queue, result_queue):
    """
    Proceso para manejar la comunicación con Civil 3D.
    """
    civil3d_app = None
    try:
        pythoncom.CoInitialize()
        acad = Autocad(create_if_not_exists=True)

        try:
            civil3d_progid = "AeccXUiLand.AeccApplication.13.7"
            civil3d_app = win32com.client.Dispatch(civil3d_progid)
            logging.info("Conexión con Civil 3D establecida en el proceso.")
        except Exception as e:
            logging.warning(f"No se pudo conectar con Civil 3D en el proceso: {e}")

        while True:
            command = command_queue.get()
            if command is None:
                logging.info("Proceso de Civil 3D terminado.")
                break

            try:
                result = perform_civil3d_operation(acad, civil3d_app, command)
                result_queue.put(result)
            except Exception as e:
                logging.error(f"Error al procesar el comando: {e}")
                result_queue.put({'error': str(e)})

    except Exception as e:
        logging.error(f"Error en el proceso Civil 3D: {e}")
    finally:
        pythoncom.CoUninitialize()
        logging.info("Finalización del proceso de Civil 3D.")

if __name__ == "__main__":
    command_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    process = multiprocessing.Process(target=civil3d_process, args=(command_queue, result_queue))
    process.start()

    coordenadas_ejemplo = [
        {'ID': 1, 'X': 0.0, 'Y': 0.0, 'Z': 0.0, 'Etiqueta': 'P1'},
        {'ID': 2, 'X': 10.0, 'Y': 0.0, 'Z': 0.0, 'Etiqueta': 'P2'}
    ]
    command_queue.put({'action': 'crear_puntos', 'coordenadas': coordenadas_ejemplo})

    command_queue.put({'action': 'seleccionar_objetos'})
    command_queue.put({'action': 'generar_polilinea', 'object_ids': ['id1', 'id2']})
    command_queue.put({'action': 'crear_tuberias', 'tuberias': [{'ID_TUBERIA': 'T1', 'PK_INICIO': 1, 'PK_FIN': 2, 'DIAMETRO': 0.3}]})

    while True:
        try:
            result = result_queue.get(timeout=10)
            if result:
                print(result)
        except queue.Empty:
            break

    command_queue.put(None)
    process.join()