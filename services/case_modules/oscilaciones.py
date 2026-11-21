"""Synthetic cabin-oscillation model using a forced damped oscillator."""

import math

from services.numerical_methods.errors import errors
from services.numerical_methods.integration import romberg, simpson, trapezoid
from services.numerical_methods.ode import rk2_system, rk4_system


def run(parameters, scenario):
    mass = float(parameters["mass"])
    damping = float(parameters["damping"])
    stiffness = float(parameters["stiffness"])
    force_amplitude = float(parameters["force"])
    forcing_frequency = float(parameters["frequency"])
    initial_position = float(parameters["x0"])
    initial_velocity = float(parameters["v0"])
    duration = float(parameters["duration"])
    requested_step = float(parameters["h"])

    if (
        not 0.05 <= mass <= 50000
        or not 0 <= damping <= 500000
        or not 0.05 <= stiffness <= 1000000
        or not 0 <= force_amplitude <= 5000
        or not 0.01 <= forcing_frequency <= 20
        or not 0.01 <= duration <= 60
        or not 0.002 <= requested_step <= 0.5
    ):
        raise ValueError(
            "M3: revise masa, amortiguamiento, rigidez, fuerza, frecuencia, "
            "duración y paso."
        )

    interval_count = max(2, math.ceil(duration / requested_step))
    if interval_count > 2000:
        raise ValueError("M3: el paso genera más de 2000 intervalos; aumente h.")
    step = duration / interval_count
    natural_frequency = math.sqrt(stiffness / mass)
    if step * max(natural_frequency, damping / mass) > 2.5:
        raise ValueError(
            "M3: el paso es grande para la frecuencia natural o el amortiguamiento; "
            "reduzca h."
        )

    def external_force(time):
        return force_amplitude * math.sin(forcing_frequency * time)

    def oscillator(time, state):
        return [
            state[1],
            (external_force(time) - damping * state[1] - stiffness * state[0]) / mass,
        ]

    solution_rk2 = rk2_system(
        oscillator, 0, [initial_position, initial_velocity], step, interval_count
    )
    solution_rk4 = rk4_system(
        oscillator, 0, [initial_position, initial_velocity], step, interval_count
    )

    # An independent, eight-times-finer RK4 trajectory acts as the comparison
    # reference for both the ODE results and the quadrature experiments.
    fine_count = interval_count * 8
    fine_step = duration / fine_count
    fine_solution = rk4_system(
        oscillator,
        0,
        [initial_position, initial_velocity],
        fine_step,
        fine_count,
    )
    coarse_reference = fine_solution[::8]
    rk2_error_curve = [
        [row["t"], abs(solution_rk2[index]["y"][0] - coarse_reference[index]["y"][0])]
        for index, row in enumerate(solution_rk2)
    ]
    rk4_error_curve = [
        [row["t"], abs(solution_rk4[index]["y"][0] - coarse_reference[index]["y"][0])]
        for index, row in enumerate(solution_rk4)
    ]
    max_rk2_error = max(point[1] for point in rk2_error_curve)
    max_rk4_error = max(point[1] for point in rk4_error_curve)

    def reference_displacement_squared(time):
        """Interpolate the fine-grid reference trajectory at an arbitrary time."""
        bounded_time = min(duration, max(0.0, time))
        index = min(fine_count - 1, max(0, int(bounded_time / fine_step)))
        fraction = (bounded_time - index * fine_step) / fine_step
        left = fine_solution[index]["y"][0]
        right = fine_solution[index + 1]["y"][0]
        displacement = left * (1 - fraction) + right * fraction
        return displacement * displacement

    # Composite Simpson on the dense reference trajectory is used as a
    # numerical reference for the separate quadrature comparison.
    integral_reference = simpson(
        reference_displacement_squared, 0, duration, fine_count
    )

    def romberg_value(requested_subintervals):
        levels = max(
            2,
            min(10, int(math.log2(max(requested_subintervals, 2))) + 1),
        )
        value, _table = romberg(reference_displacement_squared, 0, duration, levels)
        actual_subintervals = 2 ** (levels - 1)
        return value, levels, actual_subintervals

    refinements = sorted(
        set(max(2, min(interval_count, value)) for value in (2, 4, 8, 16, interval_count))
    )
    integrators = [
        (
            "trapezoid",
            "Trapecio compuesto",
            lambda count: trapezoid(
                reference_displacement_squared, 0, duration, count
            ),
        ),
        (
            "simpson",
            "Simpson 1/3",
            lambda count: simpson(
                reference_displacement_squared, 0, duration, count
            ),
        ),
    ]

    methods = []
    for code, name, rows in [
        ("rk2", "Runge-Kutta 2", solution_rk2),
        ("rk4", "Runge-Kutta 4", solution_rk4),
    ]:
        terminal_position = rows[-1]["y"][0]
        terminal_reference = coarse_reference[-1]["y"][0]
        terminal_error = errors(terminal_position, terminal_reference)
        methods.append(
            {
                "code": code,
                "name": name,
                "summary_value": terminal_position,
                "unit": "m al final del intervalo",
                "reference_value": terminal_reference,
                "error_abs": terminal_error["absolute"],
                "error_rel": terminal_error["relative"],
                "residual": None,
                "iterations": interval_count,
                "max_error": max_rk2_error if code == "rk2" else max_rk4_error,
                "steps": [
                    {
                        "n": row["n"],
                        "t": row["t"],
                        "x": row["y"][0],
                        "v": row["y"][1],
                    }
                    for row in rows
                ],
            }
        )

    quadrature_error_series = []
    for code, name, integrate in integrators:
        summary_value = integrate(interval_count)
        summary_error = errors(summary_value, integral_reference)
        steps = []
        for count in refinements:
            value = integrate(count)
            steps.append(
                {
                    "subintervals": count,
                    "value": value,
                    "error_abs": abs(value - integral_reference),
                }
            )
        methods.append(
            {
                "code": code,
                "name": name,
                "summary_value": summary_value,
                "unit": "m²·s",
                "reference_value": integral_reference,
                "error_abs": summary_error["absolute"],
                "error_rel": summary_error["relative"],
                "residual": None,
                "iterations": interval_count,
                "steps": steps,
            }
        )
        quadrature_error_series.append(
            {
                "name": name,
                "data": [[row["subintervals"], row["error_abs"]] for row in steps],
            }
        )

    romberg_summary, romberg_levels, romberg_intervals = romberg_value(interval_count)
    romberg_error = errors(romberg_summary, integral_reference)
    romberg_steps = []
    for count in refinements:
        value, levels, actual_intervals = romberg_value(count)
        romberg_steps.append(
            {
                "requested_refinement": count,
                "levels": levels,
                "subintervals": actual_intervals,
                "value": value,
                "error_abs": abs(value - integral_reference),
            }
        )
    methods.append(
        {
            "code": "romberg",
            "name": "Romberg",
            "summary_value": romberg_summary,
            "unit": "m²·s",
            "reference_value": integral_reference,
            "error_abs": romberg_error["absolute"],
            "error_rel": romberg_error["relative"],
            "residual": None,
            "iterations": romberg_levels,
            "steps": romberg_steps,
        }
    )
    quadrature_error_series.append(
        {
            "name": "Romberg",
            "data": [
                [row["subintervals"], row["error_abs"]]
                for row in romberg_steps
            ],
        }
    )

    time_points = [[row["t"], row["y"][0]] for row in solution_rk2]
    rk4_points = [[row["t"], row["y"][0]] for row in solution_rk4]
    reference_points = [
        [row["t"], row["y"][0]] for row in coarse_reference
    ]
    maximum_displacement = max(abs(row["y"][0]) for row in solution_rk4)
    frequency_ratio = forcing_frequency / natural_frequency

    return {
        "case_title": "Oscilaciones por viento",
        "scenario": scenario,
        "parameters": {
            "mass": mass,
            "damping": damping,
            "stiffness": stiffness,
            "force": force_amplitude,
            "frequency": forcing_frequency,
            "x0": initial_position,
            "v0": initial_velocity,
            "duration": duration,
            "h": step,
            "natural_frequency": natural_frequency,
            "frequency_ratio": frequency_ratio,
            "fine_reference_step": fine_step,
            "integral_reference": integral_reference,
        },
        "highlights": [
            {
                "label": "Frecuencia natural del modelo",
                "value": natural_frequency,
                "unit": "rad/s",
            },
            {
                "label": "Frecuencia externa / natural",
                "value": frequency_ratio,
                "unit": "",
            },
            {
                "label": "Desplazamiento máximo · RK4",
                "value": maximum_displacement,
                "unit": "m",
            },
            {
                "label": "Integral de referencia ∫x²dt",
                "value": integral_reference,
                "unit": "m²·s",
            },
        ],
        "methods": methods,
        "charts": [
            {
                "title": "Desplazamiento de la cabina idealizada",
                "x_label": "Tiempo (s)",
                "y_label": "Desplazamiento (m)",
                "series": [
                    {"name": "Referencia RK4 fina", "data": reference_points},
                    {"name": "RK2", "data": time_points},
                    {"name": "RK4", "data": rk4_points},
                ],
            },
            {
                "title": "Error de trayectoria frente a la referencia fina",
                "x_label": "Tiempo (s)",
                "y_label": "Error absoluto (m)",
                "series": [
                    {"name": "RK2", "data": rk2_error_curve},
                    {"name": "RK4", "data": rk4_error_curve},
                ],
            },
            {
                "title": "Error de cuadratura frente a la referencia fina",
                "x_label": "Subintervalos de refinamiento",
                "y_label": "Error absoluto de ∫x²dt (m²·s)",
                "series": quadrature_error_series,
            },
        ],
        "conclusions": {
            "numeric": (
                f"RK2 y RK4 se comparan con RK4 de paso h/8; sus errores máximos de "
                f"trayectoria son {max_rk2_error:.3g} m y {max_rk4_error:.3g} m. "
                "Las tres reglas de cuadratura muestran error absoluto respecto de una "
                "integral calculada sobre esa referencia fina."
            ),
            "case": (
                f"La relación entre frecuencia externa y natural es {frequency_ratio:.4g}. "
                "La señal, la cabina equivalente y todos los parámetros son sintéticos; "
                "una respuesta sensible cerca de la resonancia es una propiedad del "
                "modelo, no una medición de Mi Teleférico."
            ),
        },
    }
