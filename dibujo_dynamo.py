import clr
import sys

autocad_path = r"C:\Program Files\Autodesk\AutoCAD 2025"
civil3d_path = r"C:\Program Files\Autodesk\AutoCAD 2025\C3D"

if autocad_path not in sys.path:
    sys.path.append(autocad_path)
if civil3d_path not in sys.path:
    sys.path.append(civil3d_path)

clr.AddReference('AcMgd')
clr.AddReference('AcDbMgd')

from Autodesk.AutoCAD.ApplicationServices import Application
from Autodesk.AutoCAD.DatabaseServices import TransactionManager, BlockTableRecord, Line
from Autodesk.AutoCAD.Geometry import Point3d

doc = Application.DocumentManager.MdiActiveDocument

if doc:
    db = doc.Database

    try:
        with TransactionManager(db) as tm:
            bt = tm.GetObject(db.BlockTableId, OpenMode.ForRead)
            btr = tm.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite)

            start_point = Point3d(float(0), float(0), float(0))
            end_point = Point3d(float(100), float(100), float(0))
            line = Line(start_point, end_point)

            btr.AppendEntity(line)
            tm.AddNewlyCreatedDBObject(line, True)
            tm.Commit()

        OUT = "Se dibujó una línea (larga) en el documento activo."

    except Exception as e:
        OUT = f"Error al dibujar: {e}"

else:
    OUT = "No hay un documento activo de AutoCAD."