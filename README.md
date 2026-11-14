# SIMTELE-RISK · Laboratorio web

Aplicación web académica con cuatro secciones independientes: detención de emergencia, deterioro y mantenimiento, oscilaciones por viento y reconstrucción de sensores. Permite editar entradas, elegir NORMAL / ESTRÉS / MAL CONDICIONADO, ejecutar los métodos del proyecto, comparar iteraciones y errores, ver dos gráficas por módulo y guardar o recuperar corridas.

El contexto se inspira en Mi Teleférico de La Paz, Bolivia. Los escenarios y las señales son sintéticos: no representan telemetría, fallas verificadas ni controles reales.

## Inicio rápido en Windows

1. Instala Python 3.10 o posterior y descomprime el ZIP.
2. Abre la carpeta `SIMTELE_RISK_Web_Interactiva`.
3. Ejecuta `INICIAR.bat` o, desde esa carpeta, `python server.py --open-browser`.
4. Si el navegador no se abre solo, visita `http://127.0.0.1:8000`.

No requiere `pip install`: usa Python estándar, `wsgiref` y SQLite. Al iniciar se crea `instance/simtele_risk.sqlite3` con los catálogos; las corridas se guardan ahí y continúan disponibles después de cerrar y volver a iniciar el servidor.

## Qué incluye

- Panel inicial y secciones propias para M1, M2, M3 y M4.
- Entradas editables con escenarios reproducibles y validación en servidor.
- Métodos de raíces, sistemas lineales, interpolación, integración y EDO según el caso.
- Tablas de iteraciones, aproximaciones, errores y residuos.
- Dos o más gráficas dinámicas con puntos generados por el cálculo.
- Conclusión numérica y conclusión aplicada separadas.
- Historial persistente, recuperación, repetición de una corrida y descarga CSV.
- En M4, permite pegar muestras `x,y` o cargar un CSV propio de dos columnas.
- Esquema local con caso, escenario, simulación, ejecución de método, iteración y resumen.
- Entrada WSGI y guía para una posible publicación futura en PythonAnywhere.

## Alcance de esta versión

Los resultados son educativos y reproducibles con los parámetros guardados. El historial conserva las entradas y el JSON completo de resultados/gráficas para recuperar una corrida. El esquema puede normalizarse y ampliarse conforme el equipo cierre el modelo relacional definitivo. No hay autenticación; para una demo local o académica, no ingreses información privada.

## Organización

Consulta `docs/ARQUITECTURA.md` para la estructura, `docs/MODELO_DATOS.md` para la persistencia y `Guia/README.md` para el uso y la configuración WSGI futura.
