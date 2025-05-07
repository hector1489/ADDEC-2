import json
import requests
from pyautocad import Autocad

acad = Autocad()
datos_a_enviar = []

for obj in acad.iter_objects(['AcDbPoint', 'AcDbPolyline']):
    datos_objeto = {'handle': obj.Handle, 'layer': obj.Layer, 'object_name': obj.ObjectName}
    if obj.ObjectName == 'AcDbPoint':
        datos_objeto['coordinates'] = list(obj.Coordinates)
    elif obj.ObjectName == 'AcDbPolyline':
        datos_objeto['vertices'] = [list(v) for v in obj.Coordinates]
    datos_a_enviar.append(datos_objeto)

url_flask = "http://localhost:5000/recibir_datos_civil3d"
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url_flask, headers=headers, data=json.dumps(datos_a_enviar))
    if response.status_code == 200:
        print("Datos enviados correctamente a Flask.")
    else:
        print(f"Error al enviar datos a Flask: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error de conexión con Flask: {e}")