# Arquitectura de SIMTELE-RISK

## Principio

Una aplicación WSGI sirve la interfaz y la API. El mismo objeto `application` se utiliza en el servidor local (`server.py`) y como punto de entrada futuro de PythonAnywhere (`wsgi.py`). Los módulos comparten la presentación de resultados; cada problema conserva su rutina de cálculo independiente.

## Árbol de carpetas

```text
app.py                         API JSON, archivos web y manejo WSGI
server.py                      servidor de desarrollo local
wsgi.py                        punto de entrada WSGI
storage.py                     SQLite, historial y recuperación
services/case_modules/         catálogo, escenarios y cálculo M1–M4
services/numerical_methods/    familias numéricas compartidas
web/index.html                 estructura de la aplicación
web/static/app.js              navegación, formularios, tablas y gráficas
web/static/style.css           estilos adaptables a móvil y escritorio
web/static/controls.css        deslizadores y estados de validación
data/                          reservado para entradas de referencia
instance/                      base SQLite local, creada al iniciar
results/                       reservado para exportaciones
Guia/                          uso local y publicación futura
deploy/                        configuración de ejemplo para PythonAnywhere
docs/                          arquitectura, datos y ficha de escenarios
tests/                         reservado para pruebas posteriores
```

Los parámetros iniciales de los tres escenarios están declarados en `services/case_modules/__init__.py`. La API los publica en el catálogo y el navegador usa los mismos valores para llenar cada formulario. Los deslizadores muestran valores y estados de validación en tiempo real; el servidor aplica de nuevo las reglas antes del cálculo. Las entradas editadas se combinan con el preset elegido y quedan guardadas con la simulación.

## Responsabilidad de cada caso

- **M1 Detención:** raíces del modelo de frenado constante, integración de la velocidad y EDO RK2/RK4. Un ensayo separado usa `a(t)=a₀(1+γt)` para mostrar el efecto del paso temporal con desaceleración variable. El umbral de distancia es una comparación didáctica.
- **M2 Deterioro:** raíces de `D(t)=D₀+αt+βt²`, con tiempo en años simulados; Jacobi, Gauss-Seidel, LU y gradiente conjugado resuelven un sistema SPD auxiliar, separado del indicador.
- **M3 Oscilaciones:** RK2 y RK4 para un oscilador forzado. Una trayectoria RK4 con paso `h/8` sirve como referencia; Trapecio, Simpson y Romberg aproximan `∫x²dt` y reportan errores frente a una integral de referencia sobre la trayectoria fina.
- **M4 Sensores:** Lagrange, Newton por diferencias divididas y spline cúbico natural. Las muestras manuales se validan por comparación entre interpolantes cuando no hay una verdad de referencia.

Todos los valores son sintéticos. El contexto de Mi Teleférico orienta la interpretación académica, pero los modelos no describen controles ni mediciones reales.

## API local

- `GET /api/catalog` — casos, escenarios y valores iniciales.
- `POST /api/execute` — valida, calcula y guarda una corrida.
- `GET /api/history` — lista las últimas 100 corridas; acepta filtro `?case=sensores`.
- `GET /api/history/{id}` — recupera parámetros y resultados completos.
- `DELETE /api/history/{id}` — borra la corrida; las claves foráneas eliminan en cascada sus métodos, iteraciones y resumen.
- `DELETE /api/history/{id}` — borra la corrida; las claves foráneas eliminan en cascada sus métodos, iteraciones y resumen.
- `POST /api/rerun` — vuelve a calcular entradas recuperadas y guarda una nueva corrida.
- `GET /health` — estado básico del proceso y acceso a SQLite.

Las solicitudes están limitadas a JSON y se validan en el servidor. El navegador no envía código ejecutable ni consultas SQL.

## Despliegue

La plantilla WSGI puede importar la aplicación tanto localmente como en PythonAnywhere. El ZIP no contiene datos de ejecución; `instance/simtele_risk.sqlite3` se crea al importar la aplicación y la carpeta configurada debe ser escribible por el proceso WSGI.
