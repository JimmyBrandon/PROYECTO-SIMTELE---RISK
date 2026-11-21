"""Emergency-stop model and an auxiliary variable-deceleration benchmark."""

import math

from services.numerical_methods.errors import errors
from services.numerical_methods.integration import romberg, simpson, trapezoid
from services.numerical_methods.ode import rk2_system, rk4_system
from services.numerical_methods.roots import bisection, newton, secant


def run(parameters, scenario):
    v0 = float(parameters["v0"])
    reaction_time = float(parameters["tr"])
    deceleration = float(parameters["a"])
    distance_limit = float(parameters["distance_limit"])
    requested_step = float(parameters["h"])

    if (
        not 0 < v0 <= 50
        or not 0 <= reaction_time <= 30
        or not 1e-4 <= deceleration <= 20
        or not 0 < distance_limit <= 100000
        or not 0.01 <= requested_step <= 10
    ):
        raise ValueError(
            "M1: revise velocidad, tiempo de reacción, desaceleración, "
            "límite de comparación y paso temporal."
        )

    braking_time = v0 / deceleration
    reaction_distance = v0 * reaction_time
    braking_distance = v0 * v0 / (2 * deceleration)
    total_distance = reaction_distance + braking_distance
    total_time = reaction_time + braking_time
    n = max(2, math.ceil(braking_time / requested_step))
    if n > 2000:
        raise ValueError("M1: el paso genera más de 2000 intervalos; aumente h.")
    h = braking_time / n

    def constant_ode(t, state):
        return [state[1], -deceleration]

    rk2 = rk2_system(constant_ode, 0, [reaction_distance, v0], h, n)
    rk4 = rk4_system(constant_ode, 0, [reaction_distance, v0], h, n)
    velocity = lambda time: v0 - deceleration * time

    analytical_speed = [
        [i * braking_time / 100, max(0.0, velocity(i * braking_time / 100))]
        for i in range(101)
    ]
    analytical_position = [
        [
            i * braking_time / 100,
            reaction_distance
            + v0 * (i * braking_time / 100)
            - 0.5 * deceleration * (i * braking_time / 100) ** 2,
        ]
        for i in range(101)
    ]
    constant_speed = [[row["t"], max(0.0, row["y"][1])] for row in rk4]
    constant_position_2 = [[row["t"], row["y"][0]] for row in rk2]
    constant_position_4 = [[row["t"], row["y"][0]] for row in rk4]

    # The variable-deceleration run is an explicitly synthetic accuracy
    # subexperiment: a(t) = a0 * (1 + gamma*t), with gamma in 1/s.
    gamma = 0.05
    variable_stop_time = 2 * v0 / (
        deceleration + math.sqrt(deceleration**2 + 2 * deceleration * gamma * v0)
    )
    variable_braking_distance = (
        v0 * variable_stop_time
        - 0.5 * deceleration * variable_stop_time**2
        - deceleration * gamma * variable_stop_time**3 / 6
    )
    variable_total_distance = reaction_distance + variable_braking_distance
    n_variable = max(2, math.ceil(variable_stop_time / requested_step))
    if n_variable > 2000:
        raise ValueError(
            "M1: el subexperimento de desaceleración variable supera 2000 intervalos; "
            "aumente h."
        )
    h_variable = variable_stop_time / n_variable

    def variable_ode(t, state):
        return [state[1], -deceleration * (1 + gamma * t)]

    variable_rk2 = rk2_system(
        variable_ode, 0, [reaction_distance, v0], h_variable, n_variable
    )
    variable_rk4 = rk4_system(
        variable_ode, 0, [reaction_distance, v0], h_variable, n_variable
    )

    def variable_speed_exact(t):
        return max(0.0, v0 - deceleration * (t + 0.5 * gamma * t * t))

    def variable_position_exact(t):
        return (
            reaction_distance
            + v0 * t
            - 0.5 * deceleration * t**2
            - deceleration * gamma * t**3 / 6
        )

    variable_analytical_speed = [
        [i * variable_stop_time / 100, variable_speed_exact(i * variable_stop_time / 100)]
        for i in range(101)
    ]
    variable_analytical_position = [
        [
            i * variable_stop_time / 100,
            variable_position_exact(i * variable_stop_time / 100),
        ]
        for i in range(101)
    ]
    variable_position_2 = [[row["t"], row["y"][0]] for row in variable_rk2]
    variable_position_4 = [[row["t"], row["y"][0]] for row in variable_rk4]

    root_methods = [
        (
            "bisection",
            "Bisección",
            lambda: bisection(
                lambda t: v0 - deceleration * t,
                0,
                braking_time * 1.2,
            ),
        ),
        (
            "newton",
            "Newton-Raphson",
            lambda: newton(
                lambda t: v0 - deceleration * t,
                lambda _t: -deceleration,
                braking_time * 0.8,
            ),
        ),
        (
            "secant",
            "Secante",
            lambda: secant(
                lambda t: v0 - deceleration * t,
                0,
                braking_time * 1.2,
            ),
        ),
    ]
    results = []
    for code, name, solve in root_methods:
        root, steps = solve()
        root_error = errors(root, braking_time, velocity(root))
        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": root,
                "unit": "s de frenado",
                "reference_value": braking_time,
                "error_abs": root_error["absolute"],
                "error_rel": root_error["relative"],
                "residual": root_error["residual"],
                "iterations": len(steps),
                "steps": steps,
            }
        )

    refinements = sorted(set(max(2, min(n, q)) for q in (2, 4, 8, 16, n)))
    quadrature_methods = [
        (
            "trapezoid",
            "Trapecio compuesto",
            lambda count: trapezoid(velocity, 0, braking_time, count),
        ),
        (
            "simpson",
            "Simpson 1/3",
            lambda count: simpson(velocity, 0, braking_time, count),
        ),
        (
            "romberg",
            "Romberg",
            lambda count: romberg(
                velocity,
                0,
                braking_time,
                max(2, min(8, int(math.log2(max(count, 2))) + 1)),
            )[0],
        ),
    ]
    for code, name, integrate in quadrature_methods:
        value = integrate(n)
        quadrature_error = errors(value, braking_distance)
        steps = [
            {
                "subintervals": count,
                "value": integrate(count),
                "error_abs": abs(integrate(count) - braking_distance),
            }
            for count in refinements
        ]
        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": value,
                "unit": "m de frenado",
                "reference_value": braking_distance,
                "error_abs": quadrature_error["absolute"],
                "error_rel": quadrature_error["relative"],
                "residual": None,
                "iterations": n,
                "steps": steps,
            }
        )

    for code, name, rows in [
        ("rk2", "RK2 · desaceleración constante", rk2),
        ("rk4", "RK4 · desaceleración constante", rk4),
    ]:
        final_position = rows[-1]["y"][0]
        final_error = errors(final_position, total_distance)
        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": final_position,
                "unit": "m totales",
                "reference_value": total_distance,
                "error_abs": final_error["absolute"],
                "error_rel": final_error["relative"],
                "residual": None,
                "iterations": len(rows) - 1,
                "steps": [
                    {
                        "n": row["n"],
                        "t": row["t"],
                        "position": row["y"][0],
                        "speed": row["y"][1],
                    }
                    for row in rows
                ],
            }
        )

    variable_rows = [
        ("rk2_variable", "RK2 · desaceleración variable", variable_rk2),
        ("rk4_variable", "RK4 · desaceleración variable", variable_rk4),
    ]
    for code, name, rows in variable_rows:
        final_position = rows[-1]["y"][0]
        final_error = errors(final_position, variable_total_distance)
        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": final_position,
                "unit": "m totales",
                "reference_value": variable_total_distance,
                "error_abs": final_error["absolute"],
                "error_rel": final_error["relative"],
                "residual": None,
                "iterations": len(rows) - 1,
                "steps": [
                    {
                        "n": row["n"],
                        "t": row["t"],
                        "position": row["y"][0],
                        "speed": row["y"][1],
                    }
                    for row in rows
                ],
                "max_error": max(
                    abs(
                        row["y"][0]
                        - variable_position_exact(row["t"])
                    )
                    for row in rows
                ),
            }
        )

    root_residuals = [
        {
            "name": method["name"],
            "data": [
                [step["n"], abs(step.get("fx", 0.0))]
                for step in method["steps"]
            ],
        }
        for method in results[:3]
    ]
    margin = distance_limit - total_distance
    exceeded = max(0.0, -margin)

    variable_rk2_error = abs(variable_rk2[-1]["y"][0] - variable_total_distance)
    variable_rk4_error = abs(variable_rk4[-1]["y"][0] - variable_total_distance)
    numeric_conclusion = (
        f"La raíz analítica de referencia es {braking_time:.5g} s de frenado. "
        f"En el ensayo con a(t)=a₀(1+γt), γ={gamma:g} s⁻¹, "
        f"los errores finales son {variable_rk2_error:.3g} m para RK2 "
        f"y {variable_rk4_error:.3g} m para RK4."
    )
    if margin >= 0:
        comparison = f"queda un margen didáctico de {margin:.3g} m frente a {distance_limit:g} m."
    else:
        comparison = f"supera ese umbral didáctico en {exceeded:.3g} m."

    return {
        "case_title": "Detención de emergencia",
        "scenario": scenario,
        "parameters": {
            "v0": v0,
            "tr": reaction_time,
            "a": deceleration,
            "distance_limit": distance_limit,
            "h": h,
            "t_braking": braking_time,
            "t_stop_total": total_time,
            "distance_reaction": reaction_distance,
            "distance_braking": braking_distance,
            "distance_total": total_distance,
            "variable_deceleration_gamma_s_inv": gamma,
        },
        "highlights": [
            {
                "label": "Distancia total · modelo principal",
                "value": total_distance,
                "unit": "m",
            },
            {
                "label": "Tiempo total hasta detenerse",
                "value": total_time,
                "unit": "s",
            },
            {
                "label": "Comparación con umbral didáctico",
                "value": margin if margin >= 0 else exceeded,
                "unit": "m de margen" if margin >= 0 else "m de exceso",
            },
            {
                "label": "Distancia de reacción",
                "value": reaction_distance,
                "unit": "m",
            },
        ],
        "methods": results,
        "charts": [
            {
                "title": "Velocidad durante el frenado",
                "x_label": "Tiempo desde el inicio del frenado (s)",
                "y_label": "Velocidad (m/s)",
                "series": [
                    {"name": "Analítica · constante", "data": analytical_speed},
                    {"name": "RK4 · constante", "data": constant_speed},
                    {
                        "name": "Analítica · variable",
                        "data": variable_analytical_speed,
                    },
                    {
                        "name": "RK4 · variable",
                        "data": [
                            [row["t"], max(0.0, row["y"][1])]
                            for row in variable_rk4
                        ],
                    },
                ],
            },
            {
                "title": "Distancia acumulada durante el frenado",
                "x_label": "Tiempo desde el inicio del frenado (s)",
                "y_label": "Distancia total desde el inicio del viaje (m)",
                "series": [
                    {"name": "Analítica · constante", "data": analytical_position},
                    {"name": "RK2 · constante", "data": constant_position_2},
                    {"name": "RK4 · constante", "data": constant_position_4},
                    {
                        "name": "Analítica · variable",
                        "data": variable_analytical_position,
                    },
                    {"name": "RK2 · variable", "data": variable_position_2},
                    {"name": "RK4 · variable", "data": variable_position_4},
                    {
                        "name": "Umbral didáctico",
                        "data": [
                            [0, distance_limit],
                            [max(braking_time, variable_stop_time), distance_limit],
                        ],
                    },
                ],
            },
            {
                "title": "Residuo en la búsqueda del tiempo de frenado",
                "x_label": "Iteración",
                "y_label": "|v(t)| residual (m/s)",
                "series": root_residuals,
            },
        ],
        "conclusions": {
            "numeric": numeric_conclusion,
            "case": (
                f"Para este escenario académico, la distancia total del modelo principal "
                f"es {total_distance:.3g} m y {comparison} El valor de {distance_limit:g} m "
                "solo sirve para practicar la comparación; no es un límite de seguridad ni "
                "un parámetro operativo de Mi Teleférico."
            ),
        },
    }
