"""Synthetic deterioration indicator and an auxiliary SPD linear system."""

import math

from services.numerical_methods.errors import errors
from services.numerical_methods.linear import (
    condition_inf,
    conjugate_gradient,
    gauss_seidel,
    jacobi,
    lu_solve,
    residual,
)
from services.numerical_methods.roots import bisection, newton, secant


def run(parameters, scenario):
    d0 = float(parameters["d0"])
    alpha = float(parameters["alpha"])
    beta = float(parameters["beta"])
    threshold = float(parameters["threshold"])
    tolerance = float(parameters["tol"])

    if (
        not 0 <= d0 < 1
        or not 1e-6 <= alpha <= 2
        or not 0 <= beta <= 1
        or not d0 < threshold <= 10
        or not 1e-10 <= tolerance <= 1e-2
    ):
        raise ValueError("M2: parámetros fuera de rango; asegure D0 < umbral.")

    # D(t) = D0 + alpha*t + beta*t^2; t is measured in simulated years.
    def threshold_equation(time):
        return d0 + alpha * time + beta * time * time - threshold

    if beta > 1e-15:
        discriminant_root = math.sqrt(alpha * alpha + 4 * beta * (threshold - d0))
        time_reference = 2 * (threshold - d0) / (alpha + discriminant_root)
    else:
        time_reference = (threshold - d0) / alpha

    upper = max(1.0, time_reference * 1.5)
    root_solvers = [
        (
            "bisection",
            "Bisección",
            lambda: bisection(threshold_equation, 0, upper, tolerance, 300),
        ),
        (
            "newton",
            "Newton-Raphson",
            lambda: newton(
                threshold_equation,
                lambda time: alpha + 2 * beta * time,
                max(time_reference * 0.7, 1e-9),
                tolerance,
                150,
            ),
        ),
        (
            "secant",
            "Secante",
            lambda: secant(threshold_equation, 0, upper, tolerance, 150),
        ),
    ]

    results = []
    for code, name, solve in root_solvers:
        value, steps = solve()
        root_error = errors(value, time_reference, threshold_equation(value))
        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": value,
                "unit": "años simulados",
                "reference_value": time_reference,
                "error_abs": root_error["absolute"],
                "error_rel": root_error["relative"],
                "residual": root_error["residual"],
                "iterations": len(steps),
                "steps": steps,
            }
        )

    # Auxiliary four-variable SPD system. It compares linear solvers and is
    # deliberately separate from the synthetic D(t) indicator.
    if scenario == "mal_condicionado":
        matrix = [
            [1.0, 0.999, 0.0, 0.0],
            [0.999, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.999],
            [0.0, 0.0, 0.999, 1.0],
        ]
    else:
        matrix = [
            [4.0, 1.0, 0.0, 0.0],
            [1.0, 4.0, 1.0, 0.0],
            [0.0, 1.0, 4.0, 1.0],
            [0.0, 0.0, 1.0, 3.0],
        ]
    reference_vector = [1.0, 2.0, 1.0, 3.0]
    right_hand_side = [
        sum(matrix[row][column] * reference_vector[column] for column in range(4))
        for row in range(4)
    ]
    condition_number = condition_inf(matrix)

    linear_solvers = [
        ("jacobi", "Jacobi", lambda: jacobi(matrix, right_hand_side, tol=tolerance)),
        (
            "gauss_seidel",
            "Gauss-Seidel",
            lambda: gauss_seidel(matrix, right_hand_side, tol=tolerance),
        ),
        (
            "conjugate_gradient",
            "Gradiente conjugado",
            lambda: conjugate_gradient(matrix, right_hand_side, tol=tolerance),
        ),
    ]
    for code, name, solve in linear_solvers:
        solution, steps = solve()
        vector_error = math.sqrt(
            sum(
                (solution[index] - reference_vector[index]) ** 2
                for index in range(len(reference_vector))
            )
        )
        linear_residual = residual(matrix, solution, right_hand_side)
        converged = linear_residual <= tolerance
        results.append(
            {
                "code": code,
                "name": name,
                "summary_value": vector_error,
                "unit": "error vectorial",
                "reference_value": 0.0,
                "error_abs": vector_error,
                "error_rel": None,
                "residual": linear_residual,
                "iterations": len(steps),
                "converged": converged,
                "status": "Convergió" if converged else "No convergió · máximo de iteraciones",
                "steps": steps,
            }
        )

    lu_solution = lu_solve(matrix, right_hand_side)
    lu_error = math.sqrt(
        sum(
            (lu_solution[index] - reference_vector[index]) ** 2
            for index in range(len(reference_vector))
        )
    )
    lu_residual = residual(matrix, lu_solution, right_hand_side)
    results.append(
        {
            "code": "lu",
            "name": "Factorización LU",
            "summary_value": lu_error,
            "unit": "error vectorial",
            "reference_value": 0.0,
            "error_abs": lu_error,
            "error_rel": None,
            "residual": lu_residual,
            "iterations": 1,
            "converged": lu_residual <= tolerance,
            "status": "Convergió" if lu_residual <= tolerance else "No alcanzó la tolerancia numérica",
            "steps": [
                {
                    "n": 1,
                    "x": lu_solution,
                    "residual": lu_residual,
                }
            ],
        }
    )

    curve_end = max(time_reference, 1.0)
    deterioration_curve = [
        [
            curve_end * index / 100,
            d0 + alpha * (curve_end * index / 100) + beta * (curve_end * index / 100) ** 2,
        ]
        for index in range(101)
    ]
    convergence_series = [
        {
            "name": method["name"],
            "data": [
                [step.get("n", index + 1), step.get("residual", 0.0)]
                for index, step in enumerate(method["steps"])
            ],
        }
        for method in results[3:7]
    ]
    nonconverged_methods = [
        method["name"] for method in results[3:]
        if not method.get("converged", False)
    ]
    convergence_note = (
        "Todos los métodos del sistema auxiliar alcanzaron la tolerancia."
        if not nonconverged_methods
        else "No alcanzaron la tolerancia: " + ", ".join(nonconverged_methods) + ". "
        + "Se conserva la última aproximación y su residuo para analizar la convergencia."
    )

    return {
        "case_title": "Deterioro y mantenimiento",
        "scenario": scenario,
        "parameters": {
            "d0": d0,
            "alpha": alpha,
            "beta": beta,
            "threshold": threshold,
            "tol": tolerance,
            "time_unit": "años simulados",
            "matrix_order": len(matrix),
            "condition_estimate": condition_number,
            "auxiliary_matrix": matrix,
            "auxiliary_rhs": right_hand_side,
            "auxiliary_reference_solution": reference_vector,
        },
        "highlights": [
            {
                "label": "Tiempo estimado al umbral",
                "value": time_reference,
                "unit": "años simulados",
            },
            {
                "label": "Condición estimada κ∞(A)",
                "value": condition_number,
                "unit": "",
            },
            {
                "label": "Residuo del sistema auxiliar · LU",
                "value": lu_residual,
                "unit": "",
            },
            {
                "label": "Métodos comparados",
                "value": len(results),
                "unit": "algoritmos",
            },
            {
                "label": "Métodos del sistema auxiliar sin converger",
                "value": len(nonconverged_methods),
                "unit": "de 4",
            },
        ],
        "methods": results,
        "charts": [
            {
                "title": "Indicador sintético de deterioro",
                "x_label": "Tiempo (años simulados)",
                "y_label": "Indicador D(t) (u.)",
                "series": [
                    {"name": "D(t)", "data": deterioration_curve},
                    {
                        "name": "Umbral",
                        "data": [[0, threshold], [curve_end, threshold]],
                    },
                ],
            },
            {
                "title": "Residuo del sistema lineal auxiliar",
                "x_label": "Iteración",
                "y_label": "Residuo ||Ax−b||₂",
                "series": convergence_series,
            },
        ],
        "conclusions": {
            "numeric": (
                "Bisección, Newton y secante se comparan con la raíz positiva analítica "
                "de D(t)=umbral. Jacobi, Gauss-Seidel, LU y gradiente conjugado se "
                "comparan mediante error vectorial y residuo en el sistema auxiliar SPD. "
                + convergence_note
            ),
            "case": (
                f"El indicador académico alcanza el umbral cerca de {time_reference:.4g} "
                "años simulados. El sistema lineal auxiliar solo permite estudiar los "
                "métodos y el condicionamiento; ninguno de estos valores constituye una "
                "medición o un pronóstico de mantenimiento de Mi Teleférico."
            ),
        },
    }
