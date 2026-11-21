# Persistencia inicial

## Base de datos local

La aplicación crea `instance/simtele_risk.sqlite3` al iniciar. El ZIP de distribución no incluye una base de datos poblada; el primer arranque crea los catálogos y las corridas nuevas quedan guardadas en la carpeta local del proyecto.

Las tablas preliminares son:

- `caso_estudio`: catálogo de M1, M2, M3 y M4.
- `escenario`: escenarios Normal, Estrés y Mal condicionado asociados a cada caso.
- `simulacion`: fecha, estado, escenario, entradas y resultado completo serializados en JSON.
- `ejecucion_metodo`: cada método aplicado en una corrida.
- `iteracion_resultado`: pasos, iteraciones, refinamientos y aproximaciones de cada método.
- `resultado_resumen`: gráficas, conclusiones y parámetros usados.

Al borrar una simulación desde Historial, el servidor elimina la fila padre y SQLite elimina en cascada sus ejecuciones, iteraciones y resumen. La interfaz solicita confirmación antes de la petición.

El historial permite recuperar y repetir las simulaciones. La captura JSON conserva también las curvas y las estructuras específicas de cada módulo, que no tienen el mismo formato entre sí.

## Alcance del esquema

El esquema es una persistencia funcional de prototipo, no el DER definitivo. Parte de las salidas se conserva en JSON además de las tablas de método e iteraciones; esto facilita reproducir la interfaz durante el avance. Una vez cerrados los cuatro modelos y sus resultados, se puede normalizar la estructura y actualizar el DER para reflejar las entidades realmente utilizadas.

No se registra telemetría real. Para respaldar el historial local, detén el servidor y copia el archivo SQLite. La base local y una futura base alojada en PythonAnywhere serán archivos independientes.
