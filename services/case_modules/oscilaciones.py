import math
from services.numerical_methods.ode import rk2_system,rk4_system
from services.numerical_methods.integration import trapezoid,simpson,romberg

def run(p,s):
 m=float(p['mass']);c=float(p['damping']);k=float(p['stiffness']);F=float(p['force']);w=float(p['frequency']);x0=float(p['x0']);v0=float(p['v0']);duration=float(p['duration']);h=float(p['h'])
 if not .05<=m<=50000 or not 0<=c<=500000 or not .05<=k<=1000000 or not 0<=F<=5000 or not .01<=w<=20 or not .01<=duration<=60 or not .002<=h<=.5:raise ValueError('M3: revise masa, amortiguamiento, rigidez, fuerza, frecuencia, duración y paso.')
 n=max(2,math.ceil(duration/h))
 if n>2000:raise ValueError('M3: el paso genera más de 2000 intervalos; aumente h.')
 h=duration/n
 if h*max(math.sqrt(k/m),c/m)>2.5:raise ValueError('M3: el paso es grande para la frecuencia natural o el amortiguamiento; reduzca h.')
 def force(t):return F*math.sin(w*t)
 def f(t,y):return [y[1],(force(t)-c*y[1]-k*y[0])/m]
 r2=rk2_system(f,0,[x0,v0],h,n);r4=rk4_system(f,0,[x0,v0],h,n)
 # Independent fine-grid RK4 reference for validation.
 rf=rk4_system(f,0,[x0,v0],h/8,n*8)
 reference=[[q['t'],q['y'][0]] for q in rf[::8]]
 s2=[[q['t'],q['y'][0]] for q in r2];s4=[[q['t'],q['y'][0]] for q in r4]
 refmap=rf[::8];err2=max(abs(r2[i]['y'][0]-refmap[i]['y'][0]) for i in range(len(r2)));err4=max(abs(r4[i]['y'][0]-refmap[i]['y'][0]) for i in range(len(r4)))
 def x2_of_t(t):
  j=min(n-1,max(0,int(t/h)));frac=(t-j*h)/h
  x=r4[j]['y'][0]*(1-frac)+r4[j+1]['y'][0]*frac
  return x*x
 vals=[('rk2','RK2',r2,err2),('rk4','RK4',r4,err4)]
 out=[]
 for code,name,rows,err in vals:
  out.append({'code':code,'name':name,'summary_value':rows[-1]['y'][0],'unit':'m','reference_value':refmap[-1]['y'][0],'error_abs':abs(rows[-1]['y'][0]-refmap[-1]['y'][0]),'error_rel':None,'residual':None,'iterations':n,'steps':[{'n':q['n'],'t':q['t'],'x':q['y'][0],'v':q['y'][1]} for q in rows],'max_error':err})
 refinements=sorted(set(max(2,min(n,q)) for q in (2,4,8,16,n)))
 specs=[('trapecio','Trapecio',lambda q:trapezoid(x2_of_t,0,duration,q)),('simpson','Simpson 1/3',lambda q:simpson(x2_of_t,0,duration,q)),('romberg','Romberg',lambda q:romberg(x2_of_t,0,duration,max(2,min(8,int(math.log2(max(q,2)))+1)))[0])]
 for code,name,fn in specs:
  value=fn(n);steps=[{'subintervals':q,'value':fn(q)} for q in refinements]
  out.append({'code':code,'name':name,'summary_value':value,'unit':'m²·s','reference_value':None,'error_abs':None,'error_rel':None,'residual':None,'iterations':n,'steps':steps})
 errdata=[{'name':'RK2 vs RK4 fino','data':[[i*h,abs(r2[i]['y'][0]-refmap[i]['y'][0])] for i in range(0,n+1,max(1,n//60))]},{'name':'RK4 vs RK4 fino','data':[[i*h,abs(r4[i]['y'][0]-refmap[i]['y'][0])] for i in range(0,n+1,max(1,n//60))]}]
 return {'case_title':'Oscilaciones por viento','scenario':s,'parameters':{'mass':m,'damping':c,'stiffness':k,'force':F,'frequency':w,'x0':x0,'v0':v0,'duration':duration,'h':h},'methods':out,'charts':[{'title':'Desplazamiento de la cabina idealizada','x_label':'Tiempo (s)','y_label':'Desplazamiento (m)','series':[{'name':'Referencia RK4 fina','data':reference},{'name':'RK2','data':s2},{'name':'RK4','data':s4}]},{'title':'Error de trayectoria frente a referencia fina','x_label':'Tiempo (s)','y_label':'Error absoluto (m)','series':errdata}],'conclusions':{'numeric':f'RK2 y RK4 se comparan con una referencia numérica independiente calculada con paso h/8. Máximo error observado: RK2 {err2:.3g}; RK4 {err4:.3g}.','case':'La señal de fuerza y los parámetros son sintéticos. Cerca de la frecuencia natural, la amplitud puede responder con mayor sensibilidad; eso no describe una condición de operación del teleférico.'}}
