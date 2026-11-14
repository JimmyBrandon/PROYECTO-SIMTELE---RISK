import math
from services.numerical_methods.ode import rk2_system,rk4_system
from services.numerical_methods.roots import bisection,newton,secant
from services.numerical_methods.integration import trapezoid,simpson,romberg
from services.numerical_methods.errors import errors

def run(p,s):
 v0=float(p['v0']);tr=float(p['tr']);a=float(p['a']);h=float(p['h'])
 if not 0<v0<=50 or not 0<=tr<=30 or not 1e-4<=a<=20 or not 0.01<=h<=10:raise ValueError('M1: revise v0 (0–50), reacción (0–30), desaceleración (0.0001–20) y paso (0.01–10).')
 stop=v0/a;distance=v0*tr+v0*v0/(2*a);n=max(2,math.ceil(stop/h))
 if n>2000:raise ValueError('M1: el paso genera más de 2000 intervalos; aumente h.')
 h=stop/n
 def f(t):return v0-a*t
 def ode(t,y):return [y[1],-a]
 r2=rk2_system(ode,0,[v0*tr,v0],h,n);r4=rk4_system(ode,0,[v0*tr,v0],h,n)
 analytic=[[z*stop,max(0,v0-a*z*stop)] for z in [i/80 for i in range(81)]]
 speed4=[[z['t'],max(0,z['y'][1])] for z in r4]
 pos2=[[z['t'],z['y'][0]] for z in r2]
 pos4=[[z['t'],z['y'][0]] for z in r4]
 pos_analytic=[[z*stop,v0*tr+v0*z*stop-.5*a*(z*stop)**2] for z in [i/80 for i in range(81)]]
 target=lambda t:v0-a*t
 out=[]
 for code,name,solver in [('bisection','Bisección',lambda:(bisection(lambda t:v0-a*t,0,stop*1.2)[0],bisection(lambda t:v0-a*t,0,stop*1.2)[1])),('newton','Newton-Raphson',lambda:newton(lambda t:v0-a*t,lambda t:-a,stop*.8)),('secant','Secante',lambda:secant(lambda t:v0-a*t,0,stop*1.2))]:
  val,steps=solver();err=errors(val,stop,v0-a*val);out.append({'code':code,'name':name,'summary_value':val,'unit':'s','reference_value':stop,'error_abs':err['absolute'],'error_rel':err['relative'],'residual':err['residual'],'iterations':len(steps),'steps':steps})
 refinements=sorted(set(max(2,min(n,q)) for q in (2,4,8,16,n)))
 specs=[('trapecio','Trapecio compuesto',lambda q:trapezoid(target,0,stop,q)),('simpson','Simpson 1/3',lambda q:simpson(target,0,stop,q)),('romberg','Romberg',lambda q:romberg(target,0,stop,max(2,min(8,int(math.log2(max(q,2)))+1)))[0])]
 for code,name,fn in specs:
  val=fn(n);ref=v0*v0/(2*a);err=errors(val,ref);steps=[{'subintervals':q,'value':fn(q),'error_abs':abs(fn(q)-ref)} for q in refinements]
  out.append({'code':code,'name':name,'summary_value':val,'unit':'m','reference_value':ref,'error_abs':err['absolute'],'error_rel':err['relative'],'residual':None,'iterations':n,'steps':steps})
 for code,name,rows in [('rk2','Runge-Kutta 2',r2),('rk4','Runge-Kutta 4',r4)]:
  final=rows[-1]['y'];err=errors(final[0],distance);out.append({'code':code,'name':name,'summary_value':final[0],'unit':'m','reference_value':distance,'error_abs':err['absolute'],'error_rel':err['relative'],'residual':None,'iterations':len(rows)-1,'steps':[{'n':q['n'],'t':q['t'],'position':q['y'][0],'speed':q['y'][1]} for q in rows]})
 err_series=[{'name':m['name'],'data':[[q['n'],abs(q.get('fx',0))] for q in m['steps']]} for m in out[:3]]
 stop_total=tr+stop
 return {'case_title':'Detención de emergencia','scenario':s,'parameters':{'v0':v0,'tr':tr,'a':a,'h':h,'t_stop':stop_total,'distance':distance},'highlights':[{'label':'Distancia total de detención','value':distance,'unit':'m'},{'label':'Tiempo total hasta detenerse','value':stop_total,'unit':'s'},{'label':'Distancia de reacción','value':v0*tr,'unit':'m'},{'label':'Tiempo de frenado','value':stop,'unit':'s'}],'methods':out,'charts':[{'title':'Velocidad durante el frenado','x_label':'Tiempo desde el inicio del frenado (s)','y_label':'Velocidad (m/s)','series':[{'name':'Analítica','data':analytic},{'name':'RK4','data':speed4}]},{'title':'Posición acumulada desde el inicio del frenado','x_label':'Tiempo desde el inicio del frenado (s)','y_label':'Posición (m)','series':[{'name':'Analítica','data':pos_analytic},{'name':'RK2','data':pos2},{'name':'RK4','data':pos4}]},{'title':'Residuo durante la búsqueda de la raíz','x_label':'Iteración','y_label':'|v(t)| residual (m/s)','series':err_series}],'conclusions':{'numeric':'Las reglas de integración coinciden con la referencia para la velocidad lineal; RK2 y RK4 se comparan con la solución analítica. La raíz pierde sensibilidad cuando la pendiente −a es pequeña.','case':f'En este escenario sintético, el frenado toma {stop:.2f} s y la distancia total de reacción más frenado es {distance:.2f} m. No describe parámetros operativos reales.'}}
