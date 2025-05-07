document.addEventListener('DOMContentLoaded', () => {
  const formulario = document.getElementById('formularioDatos');
  const cargarDatosBtn = document.getElementById('cargarDatos');
  const ejecutarScriptBtn = document.getElementById('ejecutarScript');
  const mensajesDiv = document.getElementById('mensajes');
  const scriptSelector = document.getElementById('scriptSelector');

  cargarScripts();

  cargarDatosBtn.addEventListener('click', () => {
    mostrarSpinner();
    const coordenadasFile = document.getElementById('coordenadas').files[0];
    const tuberiasFile = document.getElementById('tuberias').files[0];

    if (!coordenadasFile || !tuberiasFile) {
      mostrarMensaje('Error: Selecciona ambos archivos CSV.', 'error');
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
    const headers = lines.shift().split(',');
    const data = [];
    lines.forEach(line => {
      const values = line.split(',');
      if (values.length === headers.length) {
        const row = {};
        for (let i = 0; i < headers.length; i++) {
          row[headers[i]] = values[i];
        }
        data.push(row);
      }
    });
    return data;
  }

  function enviarDatosAlServidor(data) {
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
  }

  function mostrarMensaje(mensaje, tipo) {
    mensajesDiv.innerHTML = `<p class="${tipo}">${mensaje}</p>`;
  }

  ejecutarScriptBtn.addEventListener('click', () => {
    mostrarSpinner();
    const scriptSeleccionado = document.getElementById('scriptSelector').value;
    fetch(`/ejecutar_script/${scriptSeleccionado}`, {
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
      window.location.href = 'csv_editor.html';
  });

  function mostrarSpinner() {
    mensajesDiv.innerHTML = '<div class="spinner"></div>';
  }
  
  function ocultarSpinner() {
    mensajesDiv.innerHTML = '';
  }
});
