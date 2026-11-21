"""Synthetic time-series reconstruction for the sensor module."""

import math

from services.numerical_methods.errors import rmse
from services.numerical_methods.interpolation import (
    lagrange,
    newton_coeff,
    newton_eval,
    spline_natural,
)


SIGNAL_AMPLITUDE_MM = 1.0
SIGNAL_PERIOD_S = 4.0
DOMAIN_START_S = 0.0
DOMAIN_END_S = 4.0


def signal_reference(time_s):
    """Evaluate the reference signal used by the reconstruction example."""
    return SIGNAL_AMPLITUDE_MM * math.sin(2 * math.pi * time_s / SIGNAL_PERIOD_S)


def parse_points(raw):
    points = []
    for line in raw.replace(";", "\n").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [value.strip() for value in line.split(",")]
        if len(parts) != 2:
            if not points and line.lower().replace(" ", "") in (
                "x,y",
                "tiempo,valor",
                "tiempo_s,lectura_mm",
            ):
                continue
            raise ValueError(
                "M4: cada fila manual debe tener dos valores separados por coma: tiempo_s,lectura_mm."
            )
        try:
            time_s, reading_mm = map(float, parts)
        except ValueError:
            if not points and parts[0].lower() in (
                "x",
                "t",
                "tiempo",
                "tiempo_s",
            ):
                continue
            raise ValueError("M4: revise las filas; use números con punto decimal.")
        if not math.isfinite(time_s) or not math.isfinite(reading_mm):
            raise ValueError("M4: las muestras deben ser números finitos.")
        points.append((time_s, reading_mm))

    if not 4 <= len(points) <= 40:
        raise ValueError("M4: ingrese entre 4 y 40 muestras manuales.")
    points.sort()
    if len({time_s for time_s, _reading in points}) != len(points):
        raise ValueError("M4: los tiempos de muestreo deben ser distintos.")
    return [time_s for time_s, _reading in points], [reading for _time, reading in points]


def run(parameters, scenario):
    requested_nodes = int(float(parameters["nodes"]))
    noise_mm = float(parameters["noise"])
    raw_points = str(parameters.get("data_points", "")).strip()
    manual_data = bool(raw_points)

    if not 4 <= requested_nodes <= 24 or not 0 <= noise_mm <= 0.5:
        raise ValueError("M4: use entre 4 y 24 nodos y ruido entre 0 y 0.5 mm.")

    base_values = None
    if manual_data:
        times_s, readings_mm = parse_points(raw_points)
        domain = (times_s[0], times_s[-1])
        candidates = [
            domain[0] + (domain[1] - domain[0]) * (index + 0.5) / 80
            for index in range(80)
        ]
        test_times = [
            time_s
            for time_s in candidates
            if min(abs(time_s - sample_time) for sample_time in times_s) > 1e-10
        ]
    else:
        times_s = [
            DOMAIN_START_S
            + (DOMAIN_END_S - DOMAIN_START_S) * index / (requested_nodes - 1)
            for index in range(requested_nodes)
        ]
        base_values = [signal_reference(time_s) for time_s in times_s]

        if scenario == "estres" and requested_nodes == 5:
            # The five training measurements receive +0.02, -0.03, ... mm
            # when the scenario's default maximum noise is 0.03 mm.
            noise_pattern = [2 / 3 if index % 2 == 0 else -1 for index in range(5)]
            perturbations = [noise_mm * factor for factor in noise_pattern]
        elif noise_mm > 0:
            perturbations = [
                noise_mm if index % 2 == 0 else -noise_mm
                for index in range(requested_nodes)
            ]
        else:
            perturbations = [0.0] * requested_nodes

        readings_mm = [
            base_values[index] + perturbations[index]
            for index in range(requested_nodes)
        ]
        domain = (DOMAIN_START_S, DOMAIN_END_S)
        if requested_nodes == 5:
            test_times = [0.5, 1.5, 2.5, 3.5]
        elif scenario == "mal_condicionado":
            test_times = [
                domain[0]
                + (domain[1] - domain[0]) * index / 1000
                for index in range(1001)
            ]
        else:
            candidates = [
                domain[0]
                + (domain[1] - domain[0]) * (index + 0.5) / 80
                for index in range(80)
            ]
            test_times = [
                time_s
                for time_s in candidates
                if min(abs(time_s - sample_time) for sample_time in times_s) > 1e-10
            ]

    divided_difference_coefficients = newton_coeff(times_s, readings_mm)

    def interpolators_for(values):
        coefficients = newton_coeff(times_s, values)
        return [
            ("lagrange", "Lagrange", lambda time_s: lagrange(times_s, values, time_s)),
            (
                "newton",
                "Newton por diferencias divididas",
                lambda time_s: newton_eval(times_s, coefficients, time_s),
            ),
            (
                "spline",
                "Spline cúbico natural",
                lambda time_s: spline_natural(times_s, values, time_s),
            ),
        ]

    methods_for_data = interpolators_for(readings_mm)
    baseline_functions = {}
    if base_values is not None and scenario == "mal_condicionado":
        baseline_functions = {
            code: function
            for code, _name, function in interpolators_for(base_values)
        }

    series = [
        {
            "name": "Muestras de entrada",
            "data": [[time_s, reading] for time_s, reading in zip(times_s, readings_mm)],
        }
    ]
    if not manual_data:
        series.append(
            {
                "name": "Referencia del modelo",
                "data": [
                    [
                        DOMAIN_START_S
                        + (DOMAIN_END_S - DOMAIN_START_S) * index / 200,
                        signal_reference(
                            DOMAIN_START_S
                            + (DOMAIN_END_S - DOMAIN_START_S) * index / 200
                        ),
                    ]
                    for index in range(201)
                ],
            }
        )

    results = []
    error_series = []
    spline_function = next(
        function for code, _name, function in methods_for_data if code == "spline"
    )
    for code, name, function in methods_for_data:
        predictions = [function(time_s) for time_s in test_times]
        curve = [
            [
                domain[0] + (domain[1] - domain[0]) * index / 200,
                function(domain[0] + (domain[1] - domain[0]) * index / 200),
            ]
            for index in range(201)
        ]
        series.append({"name": name, "data": curve})

        if manual_data:
            differences = [
                abs(value - spline_function(time_s))
                for time_s, value in zip(test_times, predictions)
            ]
            score = max(differences) if differences else 0.0
            maximum_error = None
            reference_value = None
            unit = "diferencia entre métodos (mm)"
            steps = [
                {
                    "n": index + 1,
                    "time_s": time_s,
                    "prediction_mm": value,
                    "difference_from_spline_mm": difference,
                }
                for index, (time_s, value, difference) in enumerate(
                    zip(test_times, predictions, differences)
                )
            ]
            error_series.append(
                {
                    "name": name + " vs spline",
                    "data": [[time_s, difference] for time_s, difference in zip(test_times, differences)],
                }
            )
        elif scenario == "mal_condicionado":
            baseline_function = baseline_functions[code]
            curve_changes = [
                abs(function(time_s) - baseline_function(time_s))
                for time_s in test_times
            ]
            amplification = max(curve_changes) / noise_mm if noise_mm > 0 else None
            true_errors = [
                abs(value - signal_reference(time_s))
                for time_s, value in zip(test_times, predictions)
            ]
            maximum_error = max(true_errors) if true_errors else 0.0
            score = amplification
            reference_value = None
            unit = "amplificación A"
            steps = [
                {
                    "n": index + 1,
                    "time_s": test_times[index],
                    "reference_mm": signal_reference(test_times[index]),
                    "prediction_mm": predictions[index],
                    "curve_change_mm": curve_changes[index],
                }
                for index in range(0, len(test_times), 10)
            ]
            error_series.append(
                {
                    "name": name + " · cambio de curva",
                    "data": [
                        [time_s, change]
                        for time_s, change in zip(test_times, curve_changes)
                    ],
                }
            )
        else:
            signed_errors = [
                value - signal_reference(time_s)
                for time_s, value in zip(test_times, predictions)
            ]
            absolute_errors = [abs(error) for error in signed_errors]
            maximum_error = max(absolute_errors) if absolute_errors else 0.0
            score = rmse(signed_errors)
            reference_value = 0.0
            unit = "RMSE (mm)"
            steps = [
                {
                    "n": index + 1,
                    "time_s": time_s,
                    "reference_mm": signal_reference(time_s),
                    "approximation_mm": value,
                    "error_abs_mm": absolute_error,
                }
                for index, (time_s, value, absolute_error) in enumerate(
                    zip(test_times, predictions, absolute_errors)
                )
            ]
            error_series.append(
                {
                    "name": name,
                    "data": [
                        [time_s, absolute_error]
                        for time_s, absolute_error in zip(test_times, absolute_errors)
                    ],
                }
            )

        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": score,
                "unit": unit,
                "reference_value": reference_value,
                "error_abs": maximum_error,
                "error_rel": None,
                "residual": None,
                "iterations": len(times_s),
                "steps": steps,
            }
        )

    if manual_data:
        numeric_conclusion = (
            "Con muestras manuales no hay una función exacta declarada. "
            "Por ello no se informa error real; la gráfica de diferencias compara "
            "los interpolantes con el spline natural."
        )
        applied_conclusion = (
            "Se reconstruyen únicamente las muestras ingresadas, interpretadas como "
            "tiempo en segundos y lectura en milímetros. La procedencia y el alcance "
            "del caso se describen en el informe del proyecto."
        )
    elif scenario == "mal_condicionado":
        amplification_values = [method["summary_value"] for method in results]
        if noise_mm > 0:
            amplification_text = ", ".join(
                "—" if value is None else f"{value:.3g}"
                for value in amplification_values
            )
            numeric_conclusion = (
                "Se mide A=max|pδ(t)-p(t)|/max|δᵢ| en 1001 tiempos. "
                f"Las amplificaciones de Lagrange, Newton y spline son {amplification_text}."
            )
        else:
            numeric_conclusion = (
                "Con ruido igual a cero no se define el cociente de amplificación; "
                "el cambio de curva debe ser cero."
            )
        applied_conclusion = (
            "El subexperimento aplica una perturbación definida por los parámetros "
            "actuales y compara cuánto cambia cada curva reconstruida. Su interpretación "
            "y alcance se describen en el informe del proyecto."
        )
    else:
        numeric_conclusion = (
            "Lagrange y Newton representan el mismo interpolante global, mientras que "
            "el spline cúbico natural es local por tramos. RMSE y error máximo se calculan "
            "en tiempos ocultos cuya referencia del modelo se conoce."
        )
        applied_conclusion = (
            "El caso compara métodos de reconstrucción a partir de muestras de referencia. "
            "La procedencia y los supuestos del conjunto se explican en el informe del proyecto."
        )

    return {
        "case_title": "Reconstrucción de sensores",
        "scenario": scenario,
        "parameters": {
            "nodes": len(times_s),
            "noise_input_mm": noise_mm,
            "noise_applied_mm": 0.0 if manual_data else noise_mm,
            "signal": "muestras manuales" if manual_data else "señal de referencia",
            "domain_s": [domain[0], domain[1]],
            "validation_points": len(test_times),
            "data_points": raw_points if manual_data else None,
            "newton_divided_differences": divided_difference_coefficients,
        },
        "methods": results,
        "charts": [
            {
                "title": "Reconstrucción de señal y muestras",
                "x_label": "Tiempo (s)",
                "y_label": "Lectura (mm)",
                "series": series,
            },
            {
                "title": (
                    "Diferencia entre interpolantes"
                    if manual_data
                    else (
                        "Cambio de curva ante perturbación"
                        if scenario == "mal_condicionado"
                        else "Error absoluto en tiempos ocultos"
                    )
                ),
                "x_label": "Tiempo (s)",
                "y_label": "Diferencia (mm)" if manual_data or scenario == "mal_condicionado" else "Error absoluto (mm)",
                "series": error_series,
            },
        ],
        "conclusions": {
            "numeric": numeric_conclusion,
            "case": applied_conclusion,
        },
    }
