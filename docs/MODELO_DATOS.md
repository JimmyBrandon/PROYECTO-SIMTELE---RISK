# Persistencia inicial

El archivo SQLite se crea en `instance/simtele_risk.sqlite3`, fuera de Git. Las tablas iniciales son:

- `caso_estudio`: catálogo de los cuatro módulos.
- `escenario`: escenarios Normal, Estrés y Mal condicionado por caso.
- `simulacion`: fecha, estado, escenario y captura de parámetros/resultados JSON.
- `ejecucion_metodo`: cada algoritmo ejecutado en la corrida.
- `iteracion_resultado`: pasos, iteraciones, refinamientos y aproximaciones.
- `resultado_resumen`: series para las gráficas y conclusiones guardadas.

La captura JSON permite recuperar y repetir las corridas aunque el modelo de relaciones siga en revisión. El esquema es preliminar: al cerrar el DER relacional se pueden migrar métricas, puntos de serie y configuración de gráficos a tablas más detalladas. No se registra telemetría real.

La base se inicializa con catálogos idempotentes al iniciar; el historial no se borra al reiniciar la aplicación. Para respaldar, detén el servidor y copia el archivo SQLite.
