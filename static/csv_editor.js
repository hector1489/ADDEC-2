
const tabla = document.getElementById('tablaDatos').getElementsByTagName('tbody')[0];
const encabezadoTabla = document.getElementById('tablaDatos').getElementsByTagName('thead')[0].getElementsByTagName('tr')[0];
const archivoInput = document.getElementById('archivoInput');
const guardarBoton = document.getElementById('guardarBoton');
let datosCSV = [];

archivoInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  const reader = new FileReader();

  reader.onload = (e) => {
    const csvData = e.target.result;
    cargarDatos(csvData);
  }

  reader.readAsText(file);
});

function cargarDatos(csvData) {
  const lineas = csvData.split('\n');
  const encabezado = lineas.shift().split(',');

  encabezadoTabla.innerHTML = "";
  encabezado.forEach(columna => {
    const th = document.createElement('th');
    th.textContent = columna;
    encabezadoTabla.appendChild(th);
  });

  tabla.innerHTML = "";
  datosCSV = [];

  lineas.forEach(linea => {
    const valores = linea.split(',');
    if (valores.length === encabezado.length) {
      const fila = tabla.insertRow();
      const filaData = [];
      for (let i = 0; i < valores.length; i++) {
        const celda = fila.insertCell();
        const input = document.createElement('input');
        input.type = 'text';
        input.value = valores[i];
        celda.appendChild(input);
        filaData.push(input.value);

        input.addEventListener('change', function () {
          filaData[i] = input.value;
        });
      }
      datosCSV.push(filaData);
    }
  });
}

guardarBoton.addEventListener('click', () => {
  const csvModificado = generarCSV();
  descargarArchivo(csvModificado, 'archivo_modificado.csv');
});

function generarCSV() {
  const encabezado = Array.from(encabezadoTabla.cells).map(cell => cell.textContent).join(",");
  let csv = encabezado + "\n";
  datosCSV.forEach(fila => {
    csv += fila.join(",") + "\n";
  });
  return csv;
}

function descargarArchivo(contenido, nombreArchivo) {
  const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.href = url;
  link.download = nombreArchivo;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

const agregarColumnaBoton = document.getElementById('agregarColumna');

agregarColumnaBoton.addEventListener('click', () => {
  const nombreColumna = prompt("Ingrese el nombre de la nueva columna:", "Nueva Columna");
  if (nombreColumna !== null && nombreColumna.trim() !== "") {
    agregarNuevaColumna(nombreColumna);
  }
});

function agregarNuevaColumna(nombreColumna) {
  const th = document.createElement('th');
  th.textContent = nombreColumna;
  encabezadoTabla.appendChild(th);

  for (let i = 0; i < tabla.rows.length; i++) {
    const fila = tabla.rows[i];
    const celda = fila.insertCell();
    const input = document.createElement('input');
    input.type = 'text';
    input.value = "";
    celda.appendChild(input);

    datosCSV[i].push("");
    input.addEventListener('change', function () {
      datosCSV[i][datosCSV[i].length - 1] = input.value;
    });

  }

 
}

const indexBtn = document.getElementById('indexCSV');

indexBtn.addEventListener('click', () => {
    window.location.href = 'index.html';
});



