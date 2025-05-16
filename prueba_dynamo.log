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
clr.AddReference('AeccDbMgd')

from Autodesk.AutoCAD.ApplicationServices import Application

doc = Application.DocumentManager.MdiActiveDocument
if doc:
    editor = doc.Editor
    mensaje = "\n¡Hola desde Dynamo!"
    editor.WriteMessage(mensaje)
    OUT = "Mensaje enviado a AutoCAD: " + mensaje.strip()
else:
    OUT = "No se pudo acceder al documento de AutoCAD."