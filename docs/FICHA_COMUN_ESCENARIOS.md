# Ficha común de escenarios · SIMTELE-RISK

## Alcance y uso de datos

La aplicación se inspira en el contexto general de Mi Teleférico de La Paz, Bolivia. Todos los escenarios numéricos incluidos son demostrativos y reproducibles; no son registros de operación, especificaciones de control, niveles de alerta vigentes ni diagnósticos de la empresa. Los formularios permiten editar los valores antes de cada ejecución.

Los valores iniciales se encuentran en `services/case_modules/__init__.py`. La misma configuración se entrega a la interfaz desde `GET /api/catalog` y se utiliza en el servidor al ejecutar cada módulo.

## M1 · Detención de emergencia

### Modelo principal: desaceleración constante

Se consideran por separado el recorrido durante el tiempo de reacción y el frenado:

\[
d_{reacción}=v_0t_r,\qquad t_f=\frac{v_0}{a},\qquad
d_f=\frac{v_0^2}{2a},\qquad d_{total}=d_{reacción}+d_f.
\]

La velocidad durante el frenado es `v(t)=v₀−at`. Bisección, Newton y secante buscan el tiempo en que `v(t)=0`; Trapecio, Simpson y Romberg aproximan la integral de velocidad; RK2 y RK4 integran el sistema posición-velocidad.

| Escenario | `v₀` (m/s) | `tᵣ` (s) | `a` (m/s²) | Umbral comparativo (m) | `h` (s) |
|---|---:|---:|---:|---:|---:|
| Normal | 5 | 1 | 1 | 20 | 0.1 |
| Estrés | 6 | 2 | 0.7 | 20 | 0.1 |
| Mal condicionado | 5 | 1 | 0.05 | 20 | 0.1 |

El umbral de 20 m es únicamente un valor de comparación didáctica. El ensayo adicional de desaceleración variable usa `a(t)=a₀(1+γt)`, con `γ=0.05 s⁻¹`, y su solución analítica sirve para cuantificar los errores finales de RK2 y RK4. Este ensayo también es hipotético.

## M2 · Deterioro y mantenimiento

Se define el indicador sintético `D(t)=D₀+αt+βt²`; el tiempo `t` se expresa en **años simulados** y `D` es un índice sin unidad física. Bisección, Newton y secante encuentran cuándo `D(t)` alcanza el umbral y se comparan con la raíz positiva analítica.

| Escenario | `D₀` | `α` (u./año) | `β` (u./año²) | Umbral | Tolerancia |
|---|---:|---:|---:|---:|---:|
| Normal | 0.1 | 0.025 | 0.0015 | 0.8 | 1×10⁻⁷ |
| Estrés | 0.2 | 0.06 | 0.004 | 1.1 | 1×10⁻⁷ |
| Mal condicionado | 0.1 | 0.00002 | 0.000001 | 0.8 | 1×10⁻⁷ |

Jacobi, Gauss-Seidel, LU y gradiente conjugado resuelven además un sistema SPD auxiliar `Ax=b`, con solución de referencia conocida. En el escenario mal condicionado, `A` contiene dos bloques con términos fuera de diagonal de 0.999 para estudiar sensibilidad. Este sistema es un experimento de álgebra lineal separado del indicador `D(t)`; no calibra ni pronostica el deterioro de una línea real.

## M3 · Oscilaciones por viento

El modelo masa-resorte-amortiguador es

\[
m x''+c x'+kx=F\sin(\omega t),
\]

con `x₀=0.05 m`, `v₀=0` y `ωₙ=√(k/m)`. RK2 y RK4 se comparan con una solución RK4 de paso `h/8`. Trapecio, Simpson y Romberg aproximan `∫₀ᵀ x(t)²dt`; sus errores absolutos y relativos se calculan frente a una integral de referencia evaluada sobre la trayectoria fina.

| Escenario | `m` (kg) | `c` (N·s/m) | `k` (N/m) | `F` (N) | `ω` (rad/s) | Duración (s) | `h` (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Normal | 1000 | 1000 | 30000 | 100 | 6.283185307 | 5 | 0.05 |
| Estrés | 1000 | 700 | 30000 | 160 | 6.283185307 | 10 | 0.05 |
| Mal condicionado | 1000 | 600 | 30000 | 100 | 5.4828 | 10 | 0.05 |

La proximidad entre la frecuencia externa y `ωₙ` permite estudiar sensibilidad o respuesta resonante del modelo. Los parámetros no corresponden a mediciones de una cabina.

## M4 · Reconstrucción de sensores

Lagrange y Newton producen el mismo interpolante polinómico global; el spline cúbico natural es local por tramos. En Normal y Estrés se validan tiempos ocultos cuya referencia del modelo se conoce. Si el usuario ingresa muestras propias, se informa la diferencia entre interpolantes en vez de afirmar un error real sin referencia.

| Escenario | Nodos por defecto | Configuración de ruido |
|---|---:|---|
| Normal | 5 | 0 |
| Estrés | 5 | 0.03 |
| Mal condicionado | 20 | 1×10⁻⁸ |

El formato del CSV es `tiempo_s,lectura_mm`; la aplicación acepta entre 4 y 40 muestras con tiempos distintos. La señal de referencia y la justificación de sus parámetros se describen en el informe del proyecto.

## Cómo interpretar los escenarios

- **Normal:** caso de referencia del modelo académico.
- **Estrés:** modifica parámetros para observar cómo cambia la solución dentro del modelo.
- **Mal condicionado:** enfatiza sensibilidad numérica mediante desaceleración pequeña, sistema SPD mal condicionado, frecuencia próxima a la natural o perturbación pequeña de una curva interpolada.

Los nombres sirven para organizar experimentos y comparar métodos. No clasifican la condición real de la infraestructura de Mi Teleférico.
