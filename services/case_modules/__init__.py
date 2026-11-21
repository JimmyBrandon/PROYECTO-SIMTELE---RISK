"""Case catalogue and shared scenario configuration for SIMTELE-RISK."""

from .detencion import run as run_detencion
from .deterioro import run as run_deterioro
from .oscilaciones import run as run_oscilaciones
from .sensores import run as run_sensores


CASE_INFO = [
    {
        "code": "detencion",
        "label": "M1",
        "name": "Detención de emergencia",
        "question": "¿Cómo cambian el tiempo y la distancia de detención al variar velocidad, reacción y desaceleración?",
        "notice": (
            "La comparación de 20 m es un umbral didáctico, no un límite operativo de Mi Teleférico. "
            "El ensayo de desaceleración variable también es sintético."
        ),
        "methods": [
            "RK2 · RK4",
            "Trapecio · Simpson · Romberg",
            "Bisección · Newton · Secante",
        ],
        "presets": {
            "normal": {
                "v0": 5.0,
                "tr": 1.0,
                "a": 1.0,
                "distance_limit": 20.0,
                "h": 0.1,
            },
            "estres": {
                "v0": 6.0,
                "tr": 2.0,
                "a": 0.7,
                "distance_limit": 20.0,
                "h": 0.1,
            },
            "mal_condicionado": {
                "v0": 5.0,
                "tr": 1.0,
                "a": 0.05,
                "distance_limit": 20.0,
                "h": 0.1,
            },
        },
    },
    {
        "code": "deterioro",
        "label": "M2",
        "name": "Deterioro y mantenimiento",
        "question": "¿Cuándo alcanzaría un indicador hipotético de deterioro un umbral de inspección?",
        "notice": (
            "El indicador y sus coeficientes son sintéticos y el tiempo se expresa en años simulados. "
            "El sistema lineal SPD es un ejercicio auxiliar de métodos numéricos, no una calibración real de Mi Teleférico."
        ),
        "methods": [
            "Bisección · Newton · Secante",
            "Jacobi · Gauss-Seidel · LU · Gradiente conjugado",
        ],
        "presets": {
            "normal": {
                "d0": 0.1,
                "alpha": 0.025,
                "beta": 0.0015,
                "threshold": 0.8,
                "tol": 1e-7,
            },
            "estres": {
                "d0": 0.2,
                "alpha": 0.06,
                "beta": 0.004,
                "threshold": 1.1,
                "tol": 1e-7,
            },
            "mal_condicionado": {
                "d0": 0.1,
                "alpha": 0.00002,
                "beta": 0.000001,
                "threshold": 0.8,
                "tol": 1e-7,
            },
        },
    },
    {
        "code": "oscilaciones",
        "label": "M3",
        "name": "Oscilaciones por viento",
        "question": "¿Cómo cambia la oscilación ante la fuerza externa, el amortiguamiento y los parámetros del modelo?",
        "notice": (
            "El modelo masa-resorte-amortiguador es una representación académica. "
            "La integral ∫x²dt es una medida numérica del desplazamiento al cuadrado, no energía. "
            "La fuerza, la masa y los coeficientes no son mediciones de cabinas de Mi Teleférico."
        ),
        "methods": ["RK2 · RK4", "Trapecio · Simpson · Romberg"],
        "presets": {
            "normal": {
                "mass": 1000.0,
                "damping": 1000.0,
                "stiffness": 30000.0,
                "force": 100.0,
                "frequency": 6.283185307,
                "x0": 0.05,
                "v0": 0.0,
                "duration": 5.0,
                "h": 0.05,
            },
            "estres": {
                "mass": 1000.0,
                "damping": 700.0,
                "stiffness": 30000.0,
                "force": 160.0,
                "frequency": 6.283185307,
                "x0": 0.05,
                "v0": 0.0,
                "duration": 10.0,
                "h": 0.05,
            },
            "mal_condicionado": {
                "mass": 1000.0,
                "damping": 600.0,
                "stiffness": 30000.0,
                "force": 100.0,
                "frequency": 5.4828,
                "x0": 0.05,
                "v0": 0.0,
                "duration": 10.0,
                "h": 0.05,
            },
        },
    },
    {
        "code": "sensores",
        "label": "M4",
        "name": "Reconstrucción de sensores",
        "question": "¿Cómo reconstruir muestras faltantes y medir la distorsión causada por ruido?",
        "methods": ["Lagrange · Newton por diferencias divididas · Splines cúbicos"],
        "presets": {
            "normal": {"nodes": 5, "noise": 0.0},
            "estres": {"nodes": 5, "noise": 0.03},
            "mal_condicionado": {"nodes": 20, "noise": 0.00000001},
        },
    },
]

SCENARIOS = [
    {
        "code": "normal",
        "name": "Normal",
        "description": "Parámetros sintéticos de referencia para el modelo académico.",
    },
    {
        "code": "estres",
        "name": "Estrés",
        "description": "Mayor exigencia dentro del modelo académico; no representa una contingencia real.",
    },
    {
        "code": "mal_condicionado",
        "name": "Mal condicionado",
        "description": "Subexperimento de sensibilidad numérica; no representa una falla real.",
    },
]

RUNNERS = {
    "detencion": run_detencion,
    "deterioro": run_deterioro,
    "oscilaciones": run_oscilaciones,
    "sensores": run_sensores,
}


def catalog():
    """Return cases, scenario labels, and the shared scenario presets."""
    return {"cases": CASE_INFO, "scenarios": SCENARIOS}


def run_case(request):
    code = request.get("case")
    scenario = request.get("scenario", "normal")
    params = request.get("parameters", {})

    if code not in RUNNERS:
        raise ValueError("Seleccione uno de los cuatro módulos.")
    if scenario not in {item["code"] for item in SCENARIOS}:
        raise ValueError("Seleccione un escenario válido.")
    if not isinstance(params, dict):
        raise ValueError("Los parámetros deben ser un objeto.")

    info = next(item for item in CASE_INFO if item["code"] == code)
    merged = dict(info["presets"][scenario])
    merged.update(params)
    return RUNNERS[code](merged, scenario)
