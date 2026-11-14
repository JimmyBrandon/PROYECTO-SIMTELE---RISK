import math
from services.numerical_methods.roots import bisection,newton,secant
from services.numerical_methods.linear import jacobi,gauss_seidel,lu_solve,conjugate_gradient,residual,condition_inf
from services.numerical_methods.errors import errors

def run(p,s):
 d0=float(p['d0']);alpha=float(p['alpha']);beta=float(p['beta']);thr=float(p['threshold']);tol=float(p['tol'])
 if not 0<=d0<1 or not 1e-6<=alpha<=2 or not 0<=beta<=1 or not d0<thr<=10 or not 1e-10<=tol<=1e-2:raise ValueError('M2: parámetros fuera de rango; asegure D0 < umbral.')
 f=lambda t:d0+alpha*t+beta*t*t-thr
 if beta>1e-15: exact=(-alpha+math.sqrt(alpha*alpha+4*beta*(thr-d0)))/(2*beta)
 else:exact=(thr-d0)/alpha
 hi=max(1.0,exact*1.5);out=[]
 solvers=[('bisection','Bisección',lambda:bisection(f,0,hi,tol,300)),('newton','Newton-Raphson',lambda:newton(f,lambda t:alpha+2*beta*t,max(exact*.7,1e-9),tol,150)),('secant','Secante',lambda:secant(f,0,hi,tol,150))]
 for code,name,fn in solvers:
  val,steps=fn();e=errors(val,exact,f(val));out.append({'code':code,'name':name,'summary_value':val,'unit':'tiempo','reference_value':exact,'error_abs':e['absolute'],'error_rel':e['relative'],'residual':e['residual'],'iterations':len(steps),'steps':steps})
 # Reproducible 4x4 SPD auxiliary calibration system; ill-conditioned case remains SPD.
 if s=='mal_condicionado':
  A=[[1,.999,0,0],[.999,1,0,0],[0,0,1,.999],[0,0,.999,1]]
 else:A=[[4,1,0,0],[1,4,1,0],[0,1,4,1],[0,0,1,3]]
 xref=[1,2,1,3];b=[sum(A[i][j]*xref[j] for j in range(4)) for i in range(4)];kappa=condition_inf(A)
 for code,name,fn in [('jacobi','Jacobi',lambda:jacobi(A,b,tol=tol,max_iter=500)),('gauss_seidel','Gauss-Seidel',lambda:gauss_seidel(A,b,tol=tol,max_iter=500)),('conjugate_gradient','Gradiente conjugado',lambda:conjugate_gradient(A,b,tol=tol,max_iter=100)),('lu','Factorización LU',None)]:
  if fn is None:x=lu_solve(A,b);steps=[{'n':1,'x':x,'residual':residual(A,x,b)}]
  else:x,steps=fn()
  err=math.sqrt(sum((x[i]-xref[i])**2 for i in range(4)));res=residual(A,x,b);out.append({'code':code,'name':name,'summary_value':err,'unit':'error vectorial','reference_value':0,'error_abs':err,'error_rel':None,'residual':res,'iterations':len(steps),'steps':steps})
 curve=[[i*max(exact,1)/100,d0+alpha*i*max(exact,1)/100+beta*(i*max(exact,1)/100)**2] for i in range(101)]
 conv=[]
 for m in out[3:7]:conv.append({'name':m['name'],'data':[[q.get('n',i),q.get('residual',0)] for i,q in enumerate(m['steps'])]})
 return {'case_title':'Deterioro y mantenimiento','scenario':s,'parameters':{'d0':d0,'alpha':alpha,'beta':beta,'threshold':thr,'tol':tol,'matrix_order':4,'condition_estimate':kappa},'highlights':[{'label':'Tiempo estimado al umbral','value':exact,'unit':'t'},{'label':'Condición estimada κ∞(A)','value':kappa,'unit':''},{'label':'Residuo del sistema · LU','value':out[6]['residual'],'unit':''},{'label':'Métodos comparados','value':len(out),'unit':'algoritmos'}],'methods':out,'charts':[{'title':'Indicador hipotético de deterioro','x_label':'Tiempo','y_label':'Indicador','series':[{'name':'D(t)','data':curve},{'name':'Umbral','data':[[0,thr],[curve[-1][0],thr]]}]},{'title':'Residuo por iteración · sistema lineal','x_label':'Iteración','y_label':'Residuo','series':conv}],'conclusions':{'numeric':'Se contrastan tres algoritmos de raíces y cuatro métodos para A·x=b. El caso mal condicionado usa una matriz SPD con columnas casi dependientes; el residuo y el error frente a la solución conocida se reportan por separado.','case':f'El modelo sintético alcanza el umbral cerca de t={exact:.4g}. Las entradas del deterioro y la matriz de calibración son valores demostrativos pendientes de acuerdo del equipo; no predicen mantenimiento real.'}}
