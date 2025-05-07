# DOCUEMNTACION CIVIL  3D
<<<<<<< HEAD

=======
civil 3d 2020
>>>>>>> 3a25e43 (fix update)
Este script de Python utiliza la librería pyautocad para interactuar Civil 3D.

Su función principal es leer datos de coordenadas (x, y, z) y descripciones desde un archivo CSV y luego crear puntos y textos en AutoCAD basándose en esos datos.

## Cómo usarlo

Instala las librerías: Asegúrate de tener instaladas las librerías pyautocad y csv. Puedes instalarlas con pip:

    pip install pyautocad

La librería csv viene incluida con Python, así que no necesitas instalarla.

### import

Ejecuta el script:

Abre Civil 3D y luego ejecuta el script desde la
línea de comandos o terminal:

    python crear_puntos.py

El script se conectará a Civil 3D, leerá los datos del archivo CSV y creará los puntos y textos en el dibujo.

## Descripcion

1. Importaciones:

    import csv: Importa la librería csv para trabajar con archivos CSV.
    from pyautocad import Autocad, APoint: Importa la clase Autocad para la conexión con AutoCAD y APoint para definir puntos 3D.

2. csv_file_path = 'datos.csv':

    Define la ruta al archivo CSV que contiene los datos. Debes crear este archivo y colocarlo en la misma carpeta que el script, o especificar la ruta completa.

3. leer_csv(file_path):

    Esta función lee el archivo CSV especificado en file_path.
    Utiliza csv.DictReader para leer el archivo como un diccionario, donde las claves son los encabezados de las columnas y los valores son los datos de cada fila. Es fundamental que tu archivo CSV tenga encabezados en la primera fila, por ejemplo: x,y,z,descripcion
    Maneja excepciones FileNotFoundError y otras excepciones generales para controlar errores de lectura de archivos.
    Retorna una lista de diccionarios, donde cada diccionario representa una fila del CSV.

4. data_datos = leer_csv(csv_file_path):

    Llama a la función leer_csv para cargar los datos del archivo CSV en la variable data_datos.

## POLILINEA

1. Preparación de los datos

Coordenadas:
    Necesitas las coordenadas (X, Y, Z) de los puntos de inicio y fin de cada tramo de tubería. Si no las tienes en tu archivo "CSV", tendrás que obtenerlas de alguna otra fuente (planos, levantamientos topográficos, etc.).

Curvas:
    Para los tramos curvos, necesitarás información adicional:
    Tipo de curva: (p. ej., circular, espiral, clotoide)
    Radio de la curva
    Punto de inicio y fin de la curva
    Dirección de la curva: (izquierda o derecha)

2.Importación de datos a Civil 3D

Puntos:
    Importa los puntos de inicio y fin de cada tramo de tubería a Civil 3D. Puedes usar la herramienta "Importar puntos" y seleccionar tu archivo CSV. Asegúrate de que las columnas de coordenadas (X, Y, Z) estén correctamente mapeadas.

Alineamientos:
    Crea alineamientos a partir de los puntos importados. Los alineamientos representarán la geometría de la tubería. Para los tramos rectos, puedes usar la herramienta "Crear alineación a partir de objetos". Para los tramos curvos, tendrás que usar herramientas específicas de creación de curvas (p. ej., "Curva por radio", "Curva por tres puntos").

3.Creación de la polilínea 3D

Tubería:
    Utiliza la herramienta de creación de tuberías de Civil 3D para generar la polilínea 3D. Esta herramienta te permitirá definir el diámetro, material y otras propiedades de la tubería, así como también los parámetros de las curvas.

4.Visualización y edición

Visualización:
    Visualiza la polilínea 3D en Civil 3D para verificar que se haya creado correctamente. Puedes usar diferentes estilos de visualización para representar la tubería de forma realista.

Recomendaciones adicionales

Capas: Organiza los objetos de tu dibujo en diferentes capas para facilitar su gestión y visualización.

Ejemplo de flujo de trabajo

-Obtén las coordenadas (X, Y, Z) de los puntos de inicio y fin de cada tramo de -tubería.
-Importa los puntos a Civil 3D.
-Crea alineamientos a partir de los puntos, incluyendo curvas si es necesario.
-Crea la polilínea 3D de la tubería utilizando la herramienta correspondiente.
-Visualiza y edita la polilínea 3D.

Activa tu entorno virtual si lo estás usando:
    source .venv/bin/activate
<<<<<<< HEAD
=======

python3 run.py

en windows
    .venv\Scripts\activate
    python run.py
>>>>>>> 3a25e43 (fix update)
