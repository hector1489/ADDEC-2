import csv
from pyautocad import Autocad, APoint
from flask import Blueprint, jsonify
import pythoncom
from autocad_civil import conectar_con_autocad_civil, desconectar_autocad_civil

crear_puntos_curva_bp = Blueprint('crear_puntos_curva', __name__)

COORDINATES_CSV = 'coordenadas.csv'
PIPES_CSV = 'tuberias_con_curva.csv'

def validar_coordenadas(datos):
    for fila in datos:
        try:
            x = float(fila['X'])
            y = float(fila['Y'])
            z = float(fila['Z'])
            id_punto = int(fila['ID'])
            if id_punto < 0:
                return False, "El ID del punto debe ser positivo."
        except ValueError:
            return False, f"Datos numéricos inválidos en las coordenadas: {fila}"
        except KeyError:
            return False, "Faltan columnas requeridas en las coordenadas."
    return True, None

def validar_tuberias(datos):
    for fila in datos:
        try:
            pk_inicio = int(fila['PK_INICIO'])
            pk_fin = int(fila['PK_FIN'])
            id_tuberia = fila['ID_TUBERIA']
            tipo_curva = fila.get('TIPO_CURVA')
            radio_curva = float(fila.get('RADIO_CURVA')) if fila.get('RADIO_CURVA') else None
        except ValueError:
            return False, f"Datos numéricos inválidos en la tubería: {fila}"
        except KeyError:
            return False, "Faltan columnas requeridas en las tuberías."
    return True, None

def leer_csv(ruta_archivo, required_columns=None):
    datos = []
    try:
        with open(ruta_archivo, mode='r', encoding='utf-8') as archivo:
            lector_csv = csv.DictReader(archivo)
            if required_columns and not all(col in lector_csv.fieldnames for col in required_columns):
                return None, "El archivo CSV no contiene las columnas necesarias."
            for fila in lector_csv:
                datos.append(fila)
    except FileNotFoundError:
        return None, f"Error: Archivo no encontrado: {ruta_archivo}"
    except csv.Error as e:
        return None, f"Error al procesar el archivo CSV: {e}"
    except Exception as e:
        return None, f"Error inesperado al leer el archivo {ruta_archivo}: {e}"

    return datos, None

@crear_puntos_curva_bp.route('/crear_puntos_curva')
def crear_puntos_y_tuberias():
    acad = None
    civil3d = None
    try:
        pythoncom.CoInitialize()
        acad, civil3d = conectar_con_autocad_civil()
        if not acad:
            return jsonify({'error': 'No se pudo conectar con AutoCAD.'}), 500

        datos_coordenadas, error_coordenadas = leer_csv(COORDINATES_CSV, required_columns=['X', 'Y', 'Z', 'ID', 'Etiqueta'])
        datos_tuberias, error_tuberias = leer_csv(PIPES_CSV, required_columns=['PK_INICIO', 'PK_FIN', 'ID_TUBERIA', 'TIPO_CURVA'])

        if error_coordenadas or error_tuberias:
            return jsonify({'error': error_coordenadas or error_tuberias}), 400

        valido, mensaje = validar_coordenadas(datos_coordenadas)
        if not valido:
            return jsonify({'error': mensaje}), 400

        valido, mensaje = validar_tuberias(datos_tuberias)
        if not valido:
            return jsonify({'error': mensaje}), 400

        puntos = {}

        # Crear puntos en AutoCAD
        for fila in datos_coordenadas:
            try:
                x = float(fila['X'])
                y = float(fila['Y'])
                z = float(fila['Z'])
                descripcion = fila['Etiqueta']
                id_punto = int(fila['ID'])
                punto = APoint(x, y, z)
                acad.model.AddPoint(punto)
                acad.model.AddText(descripcion, punto, 2.5)
                puntos[id_punto] = punto
            except Exception as e:
                print(f"Error al procesar el punto {fila['ID']}: {e}")
                continue

        # Crear tuberías en AutoCAD
        for fila in datos_tuberias:
            try:
                pk_inicio = int(fila['PK_INICIO'])
                pk_fin = int(fila['PK_FIN'])
                id_tuberia = fila['ID_TUBERIA']
                tipo_curva = fila['TIPO_CURVA']
                radio_curva = float(fila.get('RADIO_CURVA')) if fila.get('RADIO_CURVA') else None

                if pk_inicio in puntos and pk_fin in puntos:
                    punto_inicio = puntos[pk_inicio]
                    punto_fin = puntos[pk_fin]

                    if tipo_curva == "RECTO":
                        acad.model.AddPolyline3D([punto_inicio, punto_fin])

                    elif tipo_curva == "CURVO" and radio_curva:
                        punto_medio = APoint(
                            (punto_inicio.x + punto_fin.x) / 2,
                            (punto_inicio.y + punto_fin.y) / 2,
                            (punto_inicio.z + punto_fin.z) / 2
                        )
                        vector_direccion = punto_fin - punto_inicio
                        vector_normal = vector_direccion.normal()

                        if vector_normal.length > 0:
                            punto_central = punto_medio + vector_normal * radio_curva
                            # Para dibujar un arco, necesitas especificar el centro, radio, ángulo inicial y final.
                            # Aquí estamos asumiendo un arco de 180 grados en el plano XY.
                            # Puede que necesites ajustar esto según tus necesidades específicas (plano de la curva).
                            start_angle = 0
                            end_angle = 3.14159  # Pi (180 grados)
                            # Para asegurar que el arco va del punto inicial al final,
                            # podríamos necesitar calcular un vector perpendicular al plano de la curva
                            # y usarlo para orientar el arco. Sin más información sobre la orientación,
                            # esta es una aproximación simple en el plano XY.
                            acad.model.AddArc(punto_central, radio_curva, start_angle, end_angle)
                        else:
                            print(f"Error al calcular el vector normal para la tubería {fila['ID_TUBERIA']}")
                            continue
                    else:
                        print(f"Tipo de curva no válido o radio no especificado para la tubería {fila['ID_TUBERIA']}")
                        continue
                else:
                    print(f"PK de inicio o fin no encontrados para la tubería {fila['ID_TUBERIA']}")
                    continue

            except Exception as e:
                print(f"Error al procesar la tubería {fila['ID_TUBERIA']}: {e}")
                continue

        return jsonify({'message': 'Proceso completado correctamente.'}), 200

    except Exception as e:
        return jsonify({'error': f'Error inesperado: {e}'}), 500
    finally:
        desconectar_autocad_civil(acad, civil3d)
        try:
            pythoncom.CoUninitialize()
            print("Recursos COM liberados.")
        except Exception as e:
            print(f"Error al liberar recursos COM: {e}")