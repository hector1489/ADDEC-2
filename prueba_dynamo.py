import sys
import os

autocad_path = r"C:\Program Files\Autodesk\AutoCAD 2025"
acmgdlib_path = os.path.join(autocad_path, r"acmgdlib")

if autocad_path not in sys.path:
    sys.path.append(autocad_path)
if acmgdlib_path not in sys.path:
    sys.path.append(acmgdlib_path)

import clr
try:
    clr.AddReference('AcMgd')
    clr.AddReference('AcDbMgd')
    print("Referencias AcMgd y AcDbMgd cargadas correctamente.")
except Exception as e:
    print(f"Error al cargar referencias: {e}")

try:
    import Autodesk.AutoCAD.Layouts as Layout
    print("Módulo Autodesk.AutoCAD.Layouts importado correctamente.")
except ImportError as e:
    print(f"Error al importar Autodesk.AutoCAD.Layouts: {e}")

from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import Transaction, BlockTableRecord, Line
from Autodesk.AutoCAD.Geometry import Point2d
import Autodesk.AutoCAD.Layouts as Layout
import Autodesk.AutoCAD.DatabaseServices as ADS

doc = Application.DocumentManager.MdiActiveDocument
db = doc.Database
editor = doc.Editor

layout_manager = Layout.LayoutManager.Current

ultima_hoja_activa = layout_manager.CurrentLayout

if ultima_hoja_activa is None:
    OUT = "No se encontró un layout activo."
    editor.WriteMessage("\nNo se encontró un layout activo.")
else:
    hoja_activa_oid = layout_manager.GetLayoutId(ultima_hoja_activa)
    print(f"Layout activo encontrado: {ultima_hoja_activa}")

    punto_inicio_papel = IN[0] if IN[0] else Point2d(2, 2)
    punto_fin_papel = IN[1] if IN[1] else Point2d(8, 5)

    with Transaction(db) as t:
        try:
            hoja_activa = t.GetObject(hoja_activa_oid, Layout.Layout, ADS.OpenMode.ForRead)
            print(f"Hoja activa: {hoja_activa.Name}")

            espacio_papel_oid = hoja_activa.BlockTableRecordId
            print(f"BlockTableRecordId de la hoja activa: {espacio_papel_oid}")

            espacio_papel = t.GetObject(espacio_papel_oid, ADS.OpenMode.ForWrite)

            linea = ADS.Line(punto_inicio_papel, punto_fin_papel)
            espacio_papel.AppendEntity(linea)
            t.AddNewlyCreatedDBObject(linea, True)

            t.Commit()

            OUT = f"Línea creada correctamente en el layout: {ultima_hoja_activa}"
            editor.WriteMessage("\nLínea creada en la hoja activa.")
        except Exception as e:
            t.Abort()
            OUT = f"Error: {str(e)}"
            editor.WriteMessage(f"\nError al conectar con el layout o crear la línea: {str(e)}")