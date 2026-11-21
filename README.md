# SIMTELE-RISK · Laboratorio web

Aplicación web académica para explorar cuatro problemas de métodos numéricos inspirados en el contexto de Mi Teleférico, La Paz, Bolivia. La aplicación permite editar parámetros, ejecutar métodos, comparar errores, ver gráficas y guardar o recuperar las simulaciones.

> **Alcance de los datos:** los escenarios, señales y parámetros de simulación son sintéticos y educativos. No son telemetría, valores de control ni diagnósticos operativos de Mi Teleférico.

## Inicio rápido en Windows

1. Instala Python 3.10 o posterior y descomprime el ZIP.
2. Abre la carpeta `SIMTELE_RISK_Web_Interactiva`.
3. Ejecuta `INICIAR.bat` o, desde esa carpeta, ejecuta `python server.py --open-browser`.
4. Si el navegador no se abre automáticamente, visita `http://127.0.0.1:8000`.

No requiere instalar paquetes externos: utiliza Python estándar, `wsgiref` y SQLite. En el primer inicio crea `instance/simtele_risk.sqlite3` con los catálogos; las simulaciones se guardan allí y siguen disponibles al reiniciar.

## Módulos

- **M1 · Detención de emergencia:** tiempo y distancia de reacción y frenado; raíces, integración compuesta y EDO. Incluye un ensayo complementario con desaceleración variable para comparar RK2 y RK4. El límite de 20 m es solo didáctico.
- **M2 · Deterioro y mantenimiento:** indicador hipotético `D(t)=D₀+αt+βt²`, con tiempo expresado en años simulados; raíces y un sistema lineal SPD auxiliar para comparar métodos iterativos y directos.
- **M3 · Oscilaciones por viento:** modelo masa-resorte-amortiguador forzado; RK2 y RK4, comparación con una trayectoria RK4 fina e integración de `x²` con referencia numérica.
- **M4 · Reconstrucción de sensores:** interpolación de Lagrange, Newton y spline natural; admite muestras manuales o CSV con tiempo en segundos y lectura en milímetros.

Cada módulo conserva los escenarios **Normal**, **Estrés** y **Mal condicionado** por separado. Sus valores iniciales están definidos en el catálogo del servidor y la interfaz usa esa misma configuración. Los campos se pueden modificar antes de ejecutar.

Los parámetros se ajustan con deslizadores que muestran el valor actual y una validación inmediata por campo. El botón de ejecución se habilita cuando los valores y sus relaciones son válidos para el cálculo.

## Resultados y persistencia

- Tablas comparativas con referencia, error absoluto, error relativo, residuo y cantidad de iteraciones o pasos, cuando corresponda.
- Gráficas construidas a partir de los puntos calculados por el servidor.
- Conclusiones numéricas separadas de la interpretación del caso.
- Historial persistente, recuperación, repetición de una corrida y descarga CSV de pasos.
- Borrado individual de corridas con confirmación; al borrar una simulación, sus métodos, iteraciones y resumen asociados se eliminan en cascada.
- En los métodos iterativos de M2, el resultado indica si se alcanzó la tolerancia; si no, conserva la última aproximación, el residuo y el límite de iteraciones.
- SQLite preliminar con caso, escenario, simulación, ejecuciones de métodos, iteraciones y resumen de gráficas.

La persistencia está preparada para el prototipo. El DER definitivo podrá ajustarse cuando se cierre la estructura final de resultados de los cuatro módulos. La base SQLite se crea al iniciar; el ZIP se distribuye sin una base local ni historial de corridas.

## Carpetas y publicación

La organización actual mantiene separados el servidor WSGI, los cálculos por caso, las familias de métodos numéricos, la interfaz, la persistencia y la guía de despliegue. Consulta `docs/ARQUITECTURA.md`, `docs/FICHA_COMUN_ESCENARIOS.md`, `docs/MODELO_DATOS.md` y `Guia/README.md`.

El proyecto incluye una plantilla WSGI para PythonAnywhere, pero **todavía no está publicado**. Consulta la guía antes de desplegarlo y configura allí una ruta de base de datos escribible.
