# Arquitectura de SIMTELE-RISK

## Principio

Una aplicación WSGI sirve la interfaz y la API. El mismo objeto `application` se usa con el servidor local (`server.py`) y con PythonAnywhere (`wsgi.py`). Las cuatro páginas comparten controles visuales; cada módulo mantiene su función de cálculo en un archivo separado.

## Árbol de carpetas

```text
app.py                         API JSON, archivos web y manejo WSGI
server.py                      servidor de desarrollo local
wsgi.py                        punto de entrada WSGI
storage.py                     SQLite, historial y recuperación
services/case_modules/         cálculo por caso (M1–M4)
services/numerical_methods/    familias numéricas compartidas
web/index.html                 estructura de la aplicación
web/static/app.js              navegación, formularios, tablas y gráficas
web/static/style.css           estilos adaptables a móvil y escritorio
data/                          reservado para entradas sintéticas
instance/                      base SQLite local, no versionada
results/                       reservado para exportaciones
Guia/                          uso local y publicación futura
deploy/                        configuración de ejemplo para PythonAnywhere
docs/                          arquitectura y persistencia
tests/                         reservado para validaciones posteriores
```

## Responsabilidad de cada caso

- **M1 Detención:** RK2 y RK4, trapecio, Simpson, Romberg, bisección, Newton y secante.
- **M2 Deterioro:** bisección, Newton, secante; Jacobi, Gauss-Seidel, LU y gradiente conjugado sobre una matriz SPD.
- **M3 Oscilaciones:** RK2 y RK4 para el sistema de segundo orden; trapecio, Simpson y Romberg sobre la magnitud acumulada.
- **M4 Sensores:** Lagrange, Newton por diferencias divididas y spline cúbico natural; validación en puntos ocultos.

Cada runner devuelve una forma común: métodos con métricas y pasos, series para graficar, parámetros usados y conclusiones separadas. La interfaz no recalcula los resultados: recibe los puntos calculados por el servidor.

## API local

- `GET /api/catalog` — casos, escenarios y entradas iniciales.
- `POST /api/execute` — valida y calcula una nueva corrida, guardándola.
- `GET /api/history` — lista las últimas 100 corridas; acepta filtro `?case=sensores`.
- `GET /api/history/{id}` — recupera parámetros y resultados completos.
- `POST /api/rerun` — calcula otra vez una entrada recuperada y conserva una nueva corrida.
- `GET /health` — estado básico del proceso y acceso a SQLite.

Las entradas se limitan a JSON y pasan por validación del servidor. El sitio no acepta código, fórmulas arbitrarias ni consultas SQL del navegador.
