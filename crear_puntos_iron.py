import csv
import clr
clr.AddReference('AcMgd')
clr.AddReference('AcDbMgd')
clr.AddReference('AeccDbMgd')
clr.AddReference('AeccXUiLandMgd')

from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import Transaction, DBPoint, Point3d, Polyline3d, ObjectId, ResultBuffer, TypedValue
from Autodesk.AutoCAD.Geometry import Point2d
from Autodesk.Civil.ApplicationServices import AeccApplication
from Autodesk.Civil.DatabaseServices import Alignment

def crear_puntos_y_tuberias_desde_csv(ruta_coordenadas_csv, ruta_tuberias_csv, nombre_alineacion):
    """
    Lee datos de coordenadas y tuberías desde archivos CSV y crea puntos y líneas 3D en Civil 3D.

    Args:
        ruta_coordenadas_csv (str): Ruta al archivo CSV de coordenadas.
        ruta_tuberias_csv (str): Ruta al archivo CSV de tuberías.
        nombre_alineacion (str): Nombre de la alineación de referencia en Civil 3D.
    """
    doc = Application.DocumentManager.MdiActiveDocument
    db = doc.Database
    editor = doc.Editor
    aecc_app = AeccApplication.GetCurrentApplication()

    if not aecc_app:
        editor.WriteMessage("\nError: No se pudo obtener la aplicación de Civil 3D.")
        return

    with Transaction(db) as trans:
        try:
            # 1. Leer y crear puntos desde el archivo de coordenadas
            puntos_creados = {}
            with open(ruta_coordenadas_csv, 'r') as archivo_coordenadas_csv:
                lector_coordenadas_csv = csv.DictReader(archivo_coordenadas_csv)
                for fila_coord in lector_coordenadas_csv:
                    try:
                        id_punto = int(fila_coord['ID'])
                        x = float(fila_coord['X'])
                        y = float(fila_coord['Y'])
                        z = float(fila_coord['Z'])
                        punto_3d = Point3d(x, y, z)
                        punto_db = DBPoint(punto_3d)

                        btr = trans.GetObject(db.CurrentSpaceId, OpenMode.ForWrite)
                        btr.AppendEntity(punto_db)
                        trans.AddNewlyCreatedDBObject(punto_db, True)

                        puntos_creados[id_punto] = punto_3d  # Almacenar Point3d
                        editor.WriteMessage(f"\nPunto {id_punto} creado en ({x}, {y}, {z})")
                    except ValueError:
                        editor.WriteMessage(f"\nAdvertencia: Datos de coordenadas no válidos para el punto {fila_coord.get('ID', 'desconocido')}")
                    except KeyError as e:
                        editor.WriteMessage(f"\nError: Falta la columna '{e}' en el archivo de coordenadas: {e}")

            # 2. Leer y crear tuberías (líneas 3D) desde el archivo de tuberías
            with open(ruta_tuberias_csv, 'r') as archivo_tuberias_csv:
                lector_tuberias_csv = csv.DictReader(archivo_tuberias_csv)
                for fila_tuberia in lector_tuberias_csv:
                    try:
                        id_tuberia = fila_tuberia['ID_TUBERIA']
                        pk_inicio = int(fila_tuberia['PK_INICIO'])
                        pk_fin = int(fila_tuberia['PK_FIN'])
                        diametro = float(fila_tuberia['DIAMETRO'])
                        material = fila_tuberia['MATERIAL']
                        presion_nominal = float(fila_tuberia['PRESION_NOMINAL'])
                        conexion_inicio = fila_tuberia['CONEXION_INICIO']
                        conexion_fin = fila_tuberia['CONEXION_FIN']
                        longitud = float(fila_tuberia['LONGITUD'])
                        pendiente = float(fila_tuberia['PENDIENTE'])

                        if pk_inicio not in puntos_creados or pk_fin not in puntos_creados:
                            editor.WriteMessage(f"\nAdvertencia: Puntos de PK_INICIO ({pk_inicio}) o PK_FIN ({pk_fin}) no encontrados para la tubería {id_tuberia}. Se omite la tubería.")
                            continue

                        # Obtener los puntos 3D desde el diccionario
                        punto_inicio_3d = puntos_creados[pk_inicio]
                        punto_fin_3d = puntos_creados[pk_fin]

                        # Crear la polilínea 3D
                        pline = Polyline3d()
                        pline.SetDatabaseDefaults()
                        pline.AddVertexAt(0, punto_inicio_3d)
                        pline.AddVertexAt(1, punto_fin_3d)
                        btr.AppendEntity(pline)
                        trans.AddNewlyCreatedDBObject(pline, True)

                        # Adjuntar datos extendidos (XData) a la línea
                        reg_name = "TUBERIA_DATA"  # Nombre de registro XData
                        if not db.TryGetRegAppId(reg_name):
                            db.RegisterAppName(reg_name)
                        reg_id = db.TryGetRegAppId(reg_name)

                        xdata = ResultBuffer([
                            TypedValue(1001, reg_name),  # Aplicación de registro
                            TypedValue(1000, f"ID_TUBERIA:{id_tuberia}"),
                            TypedValue(40, diametro),
                            TypedValue(1000, f"MATERIAL:{material}"),
                            TypedValue(40, presion_nominal),
                            TypedValue(1000, f"CONEXION_INICIO:{conexion_inicio}"),
                            TypedValue(1000, f"CONEXION_FIN:{conexion_fin}"),
                            TypedValue(40, longitud),
                            TypedValue(40, pendiente)
                        ])
                        pline.XData = xdata

                        editor.WriteMessage(f"\nTubería (línea 3D) {id_tuberia} creada entre puntos {pk_inicio} y {pk_fin}.")
                    except ValueError:
                        editor.WriteMessage(f"\nAdvertencia: Datos de tubería no válidos para la tubería {fila_tuberia.get('ID_TUBERIA', 'desconocida')}")
                    except KeyError as e:
                        editor.WriteMessage(f"\nError: Falta la columna '{e}' en el archivo de tuberías: {e}")

            trans.Commit()
            editor.WriteMessage("\nProceso completado correctamente.")

        except Exception as e:
            editor.WriteMessage(f"\nError general al ejecutar el script: {e}")
            trans.Abort()
        finally:
            trans.Dispose()

# Cambia estos valores según tus archivos
ruta_archivo_coordenadas_csv = r"C:User\carlo\OneDrive\Escritorio\civil_3D_win_v\civil_3D\civil_3D\coordenadas.csv"
ruta_archivo_tuberias_csv = r"C:User\carlo\OneDrive\Escritorio\civil_3D_win_v\civil_3D\civil_3D\info_tuberias.csv"
nombre_de_la_alineacion = "ALINEA1"


crear_puntos_y_tuberias_desde_csv(ruta_archivo_coordenadas_csv, ruta_archivo_tuberias_csv, nombre_de_la_alineacion)