from .detencion import run as run_detencion
from .deterioro import run as run_deterioro
from .oscilaciones import run as run_oscilaciones
from .sensores import run as run_sensores

CASE_INFO = [
 {'code':'detencion','label':'M1','name':'Detención de emergencia','question':'¿Cómo cambian el tiempo y la distancia de detención al variar velocidad, reacción y desaceleración?','methods':['RK2 · RK4','Trapecio · Simpson · Romberg','Bisección · Newton · Secante'],'defaults':{'v0':6,'tr':1.5,'a':1.2,'h':1}},
 {'code':'deterioro','label':'M2','name':'Deterioro y mantenimiento','question':'¿Cuándo alcanzaría un indicador hipotético de deterioro un umbral de inspección?','notice':'Los valores de los escenarios y la matriz SPD de calibración son demostrativos: el informe integrado aún los deja pendientes de acuerdo del equipo.','methods':['Bisección · Newton · Secante','Jacobi · Gauss-Seidel · LU · Gradiente conjugado'],'defaults':{'d0':0.1,'alpha':0.025,'beta':0.0015,'threshold':0.8,'tol':1e-7}},
 {'code':'oscilaciones','label':'M3','name':'Oscilaciones por viento','question':'¿Cómo cambia la oscilación ante la fuerza externa, el amortiguamiento y los parámetros del modelo?','notice':'La fuerza de referencia es 100·sen(2πt) N y x₀=0.05 m, v₀=0. Los valores de m, c y k son supuestos demostrativos pendientes de confirmación.','methods':['RK2 · RK4','Trapecio · Simpson · Romberg'],'defaults':{'mass':1000,'damping':1000,'stiffness':30000,'force':100,'frequency':6.283185307,'x0':0.05,'v0':0,'duration':5,'h':0.05}},
 {'code':'sensores','label':'M4','name':'Reconstrucción de sensores','question':'¿Cómo reconstruir muestras faltantes y medir la distorsión causada por ruido?','methods':['Lagrange · Newton por diferencias divididas · Splines cúbicos'],'defaults':{'nodes':5,'noise':0}},
]
SCENARIOS=[{'code':'normal','name':'Normal','description':'Parámetros sintéticos de referencia.'},{'code':'estres','name':'Estrés','description':'Mayor exigencia dentro del modelo académico.'},{'code':'mal_condicionado','name':'Mal condicionado','description':'Subexperimento numérico sensible; no representa una falla real.'}]
RUNNERS={'detencion':run_detencion,'deterioro':run_deterioro,'oscilaciones':run_oscilaciones,'sensores':run_sensores}
def catalog():return {'cases':CASE_INFO,'scenarios':SCENARIOS}
def run_case(request):
 code=request.get('case');scenario=request.get('scenario','normal');params=request.get('parameters',{})
 if code not in RUNNERS:raise ValueError('Seleccione uno de los cuatro módulos.')
 if scenario not in {s['code'] for s in SCENARIOS}:raise ValueError('Seleccione un escenario válido.')
 if not isinstance(params,dict):raise ValueError('Los parámetros deben ser un objeto.')
 info=next(c for c in CASE_INFO if c['code']==code);merged=dict(info['defaults']);merged.update(params)
 return RUNNERS[code](merged,scenario)
