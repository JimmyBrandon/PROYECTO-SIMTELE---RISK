# Guía de uso y publicación futura

## Uso local

La aplicación puede iniciarse con doble clic en `INICIAR.bat` o con `python server.py --open-browser`. El servidor es local y queda disponible en `http://127.0.0.1:8000`. Mantén abierta la ventana del servidor mientras usas el simulador.

### Flujo de simulación

1. Elige uno de los cuatro módulos.
2. Selecciona Normal, Estrés o Mal condicionado.
3. Revisa y modifica las entradas (el escenario propone valores iniciales).
4. En M4 puedes dejar activa la señal sintética o pegar/cargar muestras propias como dos columnas `x,y`.
5. Ejecuta. La aplicación valida los datos, calcula los métodos de esa sección y guarda la corrida.
6. Revisa la comparación, tablas de pasos, errores/residuos, gráficas y las dos conclusiones.
7. Abre Historial para recuperar una corrida o repetirla; el CSV exporta las tablas de iteración.

Cada ejecución es académica y utiliza datos sintéticos. Los valores no describen el comportamiento operativo de Mi Teleférico.

## Publicación futura en PythonAnywhere

Esta entrega **no está desplegada**. La carpeta `deploy/pythonanywhere_wsgi.py` es una plantilla para más adelante; no se ejecuta desde Windows.

1. Sube el contenido del proyecto a una carpeta de tu cuenta PythonAnywhere, por ejemplo `~/simtele-risk`.
2. Crea una aplicación web de configuración manual y selecciona una versión de Python compatible.
3. En el archivo WSGI del panel, copia el contenido de `deploy/pythonanywhere_wsgi.py` y confirma que la ruta de proyecto coincide con la carpeta elegida.
4. Comprueba que `instance/` sea escribible por la aplicación. SQLite creará allí la base en el primer inicio.
5. Recarga la aplicación desde el panel Web y revisa `/health`.
6. Conserva copias de respaldo de SQLite. La base local y la alojada son archivos independientes; no se sincronizan solas.

Revisa los límites y condiciones vigentes de PythonAnywhere antes de publicar. No copies contraseñas o claves en GitHub ni en el archivo WSGI. La configuración está pensada para mantener la misma aplicación en local y bajo WSGI, sin iniciar `server.py` en la nube.
