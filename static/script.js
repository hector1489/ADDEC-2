document.addEventListener('DOMContentLoaded', () => {
  const formulario = document.getElementById('formularioDatos');
  if (!formulario) return console.error('Formulario no encontrado');

  const cargarDatosBtn = document.getElementById('cargarDatos');
  if (!cargarDatosBtn) return console.error('Botón de cargar datos no encontrado');

  const ejecutarScriptBtn = document.getElementById('ejecutarScript');
  if (!ejecutarScriptBtn) return console.error('Botón de ejecutar script no encontrado');

  const mensajesDiv = document.getElementById('mensajes');

  const scriptSelector = document.getElementById('scriptSelector');
  if (!scriptSelector) return console.error('Selector de script no encontrado');

  cargarScripts();

  cargarDatosBtn.addEventListener('click', () => {
    mostrarSpinner();
    const coordenadasFile = document.getElementById('coordenadas').files[0];
    const tuberiasFile = document.getElementById('tuberias').files[0];

    if (!coordenadasFile || !tuberiasFile) {
      mostrarMensaje('Error: Debe seleccionar ambos archivos CSV.', 'error');
      ocultarSpinner();
      return;
    }

    if (!coordenadasFile.name.endsWith('.csv') || !tuberiasFile.name.endsWith('.csv')) {
      mostrarMensaje('Error: Los archivos deben ser CSV.', 'error');
      ocultarSpinner();
      return;
    }

    Promise.all([
      leerArchivoCSV(coordenadasFile),
      leerArchivoCSV(tuberiasFile)
    ])
      .then(([coordenadasData, tuberiasData]) => {
        enviarDatosAlServidor({ coordenadas: coordenadasData, tuberias: tuberiasData });
      })
      .catch(error => {
        mostrarMensaje('Error al leer los archivos CSV: ' + error, 'error');
        ocultarSpinner();
      });
  });

  function cargarScripts() {
    fetch('/listar_scripts')
      .then(response => response.json())
      .then(scripts => {
        if (scripts.length > 0) {
          scripts.forEach(script => {
            const option = document.createElement('option');
            option.value = script;
            option.textContent = script.replace('.py', '');
            scriptSelector.appendChild(option);
          });
        } else {
          mostrarMensaje('No se encontraron scripts disponibles.', 'error');
        }
      })
      .catch(error => {
        mostrarMensaje('Error al cargar los scripts: ' + error, 'error');
      });
  }

  function leerArchivoCSV(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const csvData = e.target.result;
        const data = parseCSV(csvData);
        resolve(data);
      };
      reader.onerror = (error) => {
        reject(error);
      };
      reader.readAsText(file);
    });
  }

  function parseCSV(csvData) {
    const lines = csvData.split('\n');
    if (lines.length === 0) return [];
    const headers = lines[0].split(',');
    const data = [];
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line) {
        const values = line.split(',');
        if (values.length === headers.length) {
          const row = {};
          for (let j = 0; j < headers.length; j++) {
            row[headers[j]] = values[j];
          }
          data.push(row);
        }
      }
    }
    return data;
  }

  function enviarDatosAlServidor() {
    const archivoCoordenadasInput = document.getElementById('coordenadas');
    const archivoTuberiasInput = document.getElementById('tuberias');
  
    const archivoCoordenadas = archivoCoordenadasInput.files[0];
    const archivoTuberias = archivoTuberiasInput.files[0];
  
    if (!archivoCoordenadas || !archivoTuberias) {
      mostrarMensaje('Por favor, selecciona ambos archivos CSV.', 'error');
      return;
    }
  
    const readerCoordenadas = new FileReader();
    const readerTuberias = new FileReader();
  
    readerCoordenadas.onload = function(event) {
      const coordenadasCSV = event.target.result;
      const coordenadasArray = csvToArray(coordenadasCSV);
  
      readerTuberias.onload = function(event) {
        const tuberiasCSV = event.target.result;
        const tuberiasArray = csvToArray(tuberiasCSV);
  
        const data = {
          coordenadas: coordenadasArray,
          tuberias: tuberiasArray
        };
  
        fetch('/cargar_datos', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data)
        })
          .then(response => response.json())
          .then(mensaje => {
            mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success');
          })
          .catch(error => {
            mostrarMensaje('Error al comunicarse con el servidor: ' + error, 'error');
          });
      };
  
      readerTuberias.onerror = function() {
        mostrarMensaje('Error al leer el archivo de tuberías.', 'error');
      };
      readerTuberias.readAsText(archivoTuberias);
    };
  
    readerCoordenadas.onerror = function() {
      mostrarMensaje('Error al leer el archivo de coordenadas.', 'error');
    };
    readerCoordenadas.readAsText(archivoCoordenadas);
  }
  
  // Función para convertir texto CSV a un array de objetos JavaScript
  function csvToArray(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines.shift().split(',');
    return lines.map(line => {
      const values = line.split(',');
      return headers.reduce((obj, header, index) => {
        obj[header.trim()] = values[index] ? values[index].trim() : '';
        return obj;
      }, {});
    });
  }
  

  function mostrarMensaje(mensaje, tipo) {
    mensajesDiv.innerHTML = `<p class="${tipo}">${mensaje}</p>`;
  }

  ejecutarScriptBtn.addEventListener('click', () => {
    mostrarSpinner();
    const script_nombre = document.getElementById('scriptSelector').value;
    if (!script_nombre) {
      mostrarMensaje('Por favor, seleccione un script.', 'error');
      ocultarSpinner();
      return;
    }
    fetch(`/ejecutar_script/${script_nombre}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    })
      .then(response => response.json())
      .then(mensaje => {
        mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success');
        ocultarSpinner();
      })
      .catch(error => {
        mostrarMensaje('Error al ejecutar el script: ' + error, 'error');
        ocultarSpinner();
      });
  });

  const editarCSVBtn = document.getElementById('editarCSV');

  editarCSVBtn.addEventListener('click', () => {
    window.location.href = '/csv_editor';
  });

  function mostrarSpinner() {
    mensajesDiv.innerHTML = '<div class="spinner"></div>';
  }

  function ocultarSpinner() {
    mensajesDiv.innerHTML = '';
  }

  const seleccionarObjetosBtn = document.getElementById('seleccionarObjetos');

  seleccionarObjetosBtn.addEventListener('click', () => {
    const objectIds = obtenerIdsObjetosSeleccionados();
    if (objectIds && objectIds.length > 0) {
      enviarIdsObjetosAlServidor(objectIds);
    } else {
      mostrarMensaje('No se seleccionaron objetos.', 'error');
    }
  });

  async function obtenerIdsObjetosSeleccionados() {
    try {
      const response = await fetch('/seleccionar_objetos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });
      const data = await response.json();
      if (data.object_ids && data.object_ids.length > 0) {
        generarPolilinea(data.object_ids);
      } else {
        mostrarMensaje('No se encontraron objetos para seleccionar.', 'error');
      }
      return data.object_ids;
    } catch (error) {
      console.error('Error al obtener IDs de objetos:', error);
      return [];
    }
  }

  function generarPolilinea(objectIds) {
    fetch('/generar_polilinea', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ object_ids: objectIds })
    })
      .then(response => response.json())
      .then(mensaje => {
        mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success');
      })
      .catch(error => {
        mostrarMensaje('Error al generar polilínea: ' + error, 'error');
      });
  }

  const generarPerfilTerrenoBtn = document.getElementById('generarPerfilTerreno');
  const copiarPerfilTapadoBtn = document.getElementById('copiarPerfilTapado');
  const copiarRasanteBtn = document.getElementById('copiarRasante');
  const minimizarVerticesRasanteBtn = document.getElementById('minimizarVerticesRasante');

  generarPerfilTerrenoBtn.addEventListener('click', () => {
    const alineamientoId = prompt('Ingrese el ID del alineamiento:');
    const polilineaId = prompt('Ingrese el ID de la polilínea 3D:');

    if (alineamientoId && polilineaId) {
      fetch('/generar_perfil_terreno', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ alineamiento_id: alineamientoId, polilinea_id: polilineaId })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese los IDs del alineamiento y la polilínea.', 'error');
    }
  });

  copiarPerfilTapadoBtn.addEventListener('click', () => {
    const perfilId = prompt('Ingrese el ID del perfil:');
    const distanciaTapa = prompt('Ingrese la distancia de la tapa:');

    if (perfilId && distanciaTapa) {
      fetch('/copiar_perfil_tapado', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ perfil_id: perfilId, distancia_tapa: parseFloat(distanciaTapa) })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese el ID del perfil y la distancia de la tapa.', 'error');
    }
  });

  copiarRasanteBtn.addEventListener('click', () => {
    const perfilId = prompt('Ingrese el ID del perfil:');

    if (perfilId) {
      fetch('/copiar_rasante', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ perfil_id: perfilId })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese el ID del perfil.', 'error');
    }
  });

  minimizarVerticesRasanteBtn.addEventListener('click', () => {
    const rasanteId = prompt('Ingrese el ID de la rasante:');
    const tolerancia = prompt('Ingrese la tolerancia de simplificación:');

    if (rasanteId && tolerancia) {
      fetch('/minimizar_vertices_rasante', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rasante_id: rasanteId, tolerancia: parseFloat(tolerancia) })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese el ID de la rasante y la tolerancia.', 'error');
    }
  });

  const etiquetarVerticesVerticalesBtn = document.getElementById('etiquetarVerticesVerticales');
  const etiquetarVerticesHorizontalesBtn = document.getElementById('etiquetarVerticesHorizontales');
  const etiquetarDistanciasBtn = document.getElementById('etiquetarDistancias');

  etiquetarVerticesVerticalesBtn.addEventListener('click', () => {
    const perfilId = prompt('Ingrese el ID del perfil:');

    if (perfilId) {
      fetch('/etiquetar_vertices_verticales', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ perfil_id: perfilId })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese el ID del perfil.', 'error');
    }
  });

  etiquetarVerticesHorizontalesBtn.addEventListener('click', () => {
    const alineamientoId = prompt('Ingrese el ID del alineamiento:');

    if (alineamientoId) {
      fetch('/etiquetar_vertices_horizontales', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ alineamiento_id: alineamientoId })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese el ID del alineamiento.', 'error');
    }
  });

  etiquetarDistanciasBtn.addEventListener('click', () => {
    const polilineaId = prompt('Ingrese el ID de la polilínea:');
    const puntoRefX = prompt('Ingrese la coordenada X del punto de referencia:');
    const puntoRefY = prompt('Ingrese la coordenada Y del punto de referencia:');
    const puntoRefZ = prompt('Ingrese la coordenada Z del punto de referencia:');

    if (polilineaId && puntoRefX && puntoRefY && puntoRefZ) {
      fetch('/etiquetar_distancias', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          polilinea_id: polilineaId,
          punto_referencia: {
            x: parseFloat(puntoRefX),
            y: parseFloat(puntoRefY),
            z: parseFloat(puntoRefZ)
          }
        })
      })
        .then(response => response.json())
        .then(mensaje => mostrarMensaje(mensaje.message, mensaje.error ? 'error' : 'success'))
        .catch(error => mostrarMensaje('Error: ' + error, 'error'));
    } else {
      mostrarMensaje('Por favor, ingrese el ID de la polilínea y las coordenadas del punto de referencia.', 'error');
    }
  });

  document.getElementById('verObjetos').addEventListener('click', function() {
    fetch('/obtener_objetos')
        .then(response => response.json())
        .then(data => {
            const jsonOutputDiv = document.getElementById('jsonOutput');
            jsonOutputDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 4) + '</pre>';
        })
        .catch(error => {
            const jsonOutputDiv = document.getElementById('jsonOutput');
            jsonOutputDiv.innerHTML = `<p style="color: red;">Error al obtener los objetos de AutoCAD: ${error}</p>`;
        });
  });

  document.getElementById('verPerfiles').addEventListener('click', function() {
    fetch('/obtener_perfiles')
        .then(response => response.json())
        .then(data => {
            const jsonOutputDiv = document.getElementById('jsonOutput');
            jsonOutputDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 4) + '</pre>';
        })
        .catch(error => {
            const jsonOutputDiv = document.getElementById('jsonOutput');
            jsonOutputDiv.innerHTML = `<p style="color: red;">Error al obtener los perfiles de AutoCAD: ${error}</p>`;
        });



  });

 


});


document.getElementById('abrirDWGBtn').addEventListener('click', function(event) {
  event.preventDefault();

  const archivoInput = document.getElementById('archivoDWG');
  const archivoDWG = archivoInput.files[0];

  if (!archivoDWG) {
      document.getElementById('jsonOutput').innerHTML = '<p style="color: red;">Por favor selecciona un archivo DWG.</p>';
      return;
  }

  console.log('Archivo seleccionado:', archivoDWG);

  const formData = new FormData();
  formData.append('archivo_dwg', archivoDWG);

  fetch('/abrir_dwg', {
      method: 'POST', 
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      const jsonOutputDiv = document.getElementById('jsonOutput');
      jsonOutputDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 4) + '</pre>';
  })
  .catch(error => {
      const jsonOutputDiv = document.getElementById('jsonOutput');
      jsonOutputDiv.innerHTML = `<p style="color: red;">Error al abrir el archivo DWG: ${error}</p>`;
      console.error('Error en la carga del archivo:', error);
  });
});


