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
from Autodesk.AutoCAD.DatabaseServices import OpenMode, BlockTable, BlockTableRecord, Line
from Autodesk.AutoCAD.Geometry import Point3d

doc = Application.DocumentManager.MdiActiveDocument

if doc:
    db = doc.Database
    tr = None
    try:
        tr = db.TransactionManager.StartTransaction()

        OUT = []

        bt = tr.GetObject(db.BlockTableId, OpenMode.ForRead)
        OUT.append("BlockTable obtenido")
        OUT.append("Tipo de bt: " + str(type(bt)))

        model_space_id = bt.GetAt("ModelSpace")
        OUT.append("ModelSpace ObjectId obtenido")

        btr = tr.GetObject(model_space_id, OpenMode.ForWrite)
        OUT.append("BlockTableRecord del espacio modelo obtenido")

        start_point = Point3d(0, 0, 0)
        end_point = Point3d(100, 100, 0)
        line = Line(start_point, end_point)

        btr.AppendEntity(line)
        tr.AddNewlyCreatedDBObject(line, True)
        OUT.append("Línea añadida al espacio modelo")

        tr.Commit()
        OUT.append("Transacción realizada correctamente")

    except Exception as e:
        OUT = ["Error durante la ejecución:", str(e)]

    finally:
        if tr is not None:
            tr.Dispose()
else:
    OUT = ["No hay un documento activo en AutoCAD."]
