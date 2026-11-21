# Guía de uso y publicación futura

## Uso local

La aplicación puede iniciarse con doble clic en `INICIAR.bat` o desde la carpeta del proyecto con `python server.py --open-browser`. El servidor local queda disponible en `http://127.0.0.1:8000`. Mantén abierta la ventana del servidor mientras utilizas el simulador.

## Flujo de simulación

1. Elige uno de los cuatro módulos.
2. Selecciona Normal, Estrés o Mal condicionado. Cada uno carga sus propios valores iniciales.
3. Mueve los deslizadores para modificar las entradas. El valor actual y su estado de validación aparecen junto a cada control; las relaciones incompatibles entre parámetros deshabilitan la ejecución hasta corregirlas.
4. En M4 puedes usar la demostración sintética o pegar/cargar muestras CSV de dos columnas: tiempo en segundos y lectura en milímetros.
5. Ejecuta la simulación. La aplicación calcula los métodos del módulo y guarda la corrida.
6. Revisa la comparación de métodos, las iteraciones, los errores, las gráficas y las conclusiones numéricas y de contexto.
7. Abre Historial para recuperar una corrida o repetirla. Puedes borrar una corrida desde su botón Borrar y confirmar en el diálogo. El botón CSV descarga las tablas de pasos.

La configuración y la procedencia del conjunto de referencia de M4 se explican en el informe del proyecto. El umbral comparativo de M1 y los demás valores de los casos son parte de modelos didácticos.

## Publicación futura en PythonAnywhere

Esta entrega **no está desplegada**. `deploy/pythonanywhere_wsgi.py` es una plantilla para una configuración futura; no se ejecuta desde Windows.

1. Sube el contenido del proyecto a una carpeta de tu cuenta PythonAnywhere, por ejemplo `~/simtele-risk`.
2. Crea una aplicación web de configuración manual y elige una versión compatible de Python.
3. En el archivo WSGI del panel, copia el contenido de `deploy/pythonanywhere_wsgi.py` y confirma que la ruta del proyecto corresponda a tu carpeta.
4. Configura `SIMTELE_DB` con una ruta escribible por la aplicación, o asegúrate de que la carpeta `instance/` tenga permisos de escritura.
5. Recarga la aplicación desde el panel Web y revisa `/health`.
6. Conserva copias de respaldo de SQLite. La base local y la alojada son archivos independientes y no se sincronizan automáticamente.

No subas datos privados ni claves al repositorio. Revisa las condiciones vigentes de PythonAnywhere antes de publicar.
