import csv
import clr
clr.AddReference('AcMgd')
clr.AddReference('AcDbMgd')
clr.AddReference('AeccDbMgd')
clr.AddReference('AeccXUiLandMgd')

from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import Transaction, DBPoint, ObjectId
from Autodesk.AutoCAD.Geometry import Point3d
from Autodesk.Civil.ApplicationServices import AeccApplication
from Autodesk.Civil.DatabaseServices import Alignment

def crear_puntos_en_alineacion_desde_csv(ruta_csv, nombre_alineacion):
    """
    Lee un archivo CSV con datos de tuberías y crea puntos en una alineación de Civil 3D
    en las ubicaciones de PK de inicio y fin.
    """
    try:
        doc = Application.DocumentManager.MdiActiveDocument
        db = doc.Database
        editor = doc.Editor
        aecc_app = AeccApplication.GetCurrentApplication()
        if not aecc_app:
            editor.WriteMessage("\nError: No se pudo obtener la aplicación de Civil 3D.")
            return

        with Transaction(db) as t:
            # Encontrar la alineación por nombre
            alineacion_oid = ObjectId.Null
            for oid in db.CurrentSpaceId:
                ent = t.GetObject(oid, Autodesk.AutoCAD.DatabaseServices.OpenMode.ForRead)
                if isinstance(ent, Alignment) and ent.Name == nombre_alineacion:
                    alineacion_oid = oid
                    break

            if alineacion_oid == ObjectId.Null:
                editor.WriteMessage(f"\nError: No se encontró la alineación con el nombre '{nombre_alineacion}'.")
                return

            alineacion = t.GetObject(alineacion_oid, Autodesk.AutoCAD.DatabaseServices.OpenMode.ForRead)

            with open(ruta_csv, 'r') as archivo_csv:
                lector_csv = csv.DictReader(archivo_csv)
                for fila in lector_csv:
                    try:
                        pk_inicio = float(fila['PK_INICIO'])
                        pk_fin = float(fila['PK_FIN'])
                        id_tuberia = fila['ID_TUBERIA']

                        # Obtener punto en la alineación por PK de inicio
                        pto_inicio = alineacion.StationOffsetElevation(pk_inicio, 0.0)
                        punto_inicio_3d = Point3d(pto_inicio.X, pto_inicio.Y, pto_inicio.Z)

                        # Obtener punto en la alineación por PK de fin
                        pto_fin = alineacion.StationOffsetElevation(pk_fin, 0.0)
                        punto_fin_3d = Point3d(pto_fin.X, pto_fin.Y, pto_fin.Z)

                        # Crear puntos de AutoCAD en el dibujo
                        espacio_modelo = t.GetObject(db.CurrentSpaceId, Autodesk.AutoCAD.DatabaseServices.OpenMode.ForWrite)
                        punto_inicio_db = DBPoint(punto_inicio_3d)
                        punto_fin_db = DBPoint(punto_fin_3d)
                        espacio_modelo.AppendEntity(punto_inicio_db)
                        espacio_modelo.AppendEntity(punto_fin_db)
                        t.AddNewlyCreatedDBObject(punto_inicio_db, True)
                        t.AddNewlyCreatedDBObject(punto_fin_db, True)

                        editor.WriteMessage(f"\nPuntos creados para tubería {id_tuberia} en PK Inicio: {pk_inicio}, PK Fin: {pk_fin}")

                    except ValueError:
                        editor.WriteMessage(f"\nAdvertencia: Valores de PK no válidos para la tubería {fila.get('ID_TUBERIA', 'desconocida')}.")
                    except KeyError as e:
                        editor.WriteMessage(f"\nError: Falta la columna '{e}' en el archivo CSV.")

            t.Commit()
            editor.WriteMessage("\nProceso completado: Puntos creados en la alineación.")

    except Exception as e:
        editor.WriteMessage(f"\nError general al ejecutar el script: {e}")

ruta_archivo_csv = r"C:\ruta\a\tu\archivo.csv"
nombre_de_la_alineacion = "Nombre de tu Alineación"

crear_puntos_en_alineacion_desde_csv(ruta_archivo_csv, nombre_de_la_alineacion)