import math
from services.numerical_methods.interpolation import lagrange,newton_coeff,newton_eval,spline_natural
from services.numerical_methods.errors import rmse

def parse_points(raw):
 points=[]
 for line in raw.replace(';','\n').splitlines():
  line=line.strip()
  if not line:continue
  parts=[x.strip() for x in line.split(',')]
  if len(parts)!=2:
   if not points and line.lower().replace(' ','') in ('x,y','tiempo,valor'):continue
   raise ValueError('M4: cada fila manual debe tener dos valores separados por coma: x,y.')
  try:x,y=map(float,parts)
  except ValueError:
   if not points and parts[0].lower() in ('x','t','tiempo'):continue
   raise ValueError('M4: revise las filas; use números con punto decimal.')
  if not math.isfinite(x) or not math.isfinite(y):raise ValueError('M4: las muestras deben ser números finitos.')
  points.append((x,y))
 if not 4<=len(points)<=40:raise ValueError('M4: ingrese entre 4 y 40 muestras manuales.')
 points.sort()
 if len({x for x,_ in points})!=len(points):raise ValueError('M4: las coordenadas x deben ser distintas.')
 return [x for x,_ in points],[y for _,y in points]

def run(p,s):
 nodes=int(float(p['nodes']));noise=float(p['noise']);raw=str(p.get('data_points','')).strip();manual=bool(raw)
 if not 4<=nodes<=24 or not 0<=noise<=0.5:raise ValueError('M4: use entre 4 y 24 nodos y ruido entre 0 y 0.5.')
 if manual:
  xs,ys=parse_points(raw);ys0=None;test=[xs[0]+(xs[-1]-xs[0])*(i+.5)/80 for i in range(80)];domain=(xs[0],xs[-1])
 else:
  end=2*math.pi if s=='estres' else math.pi
  xs=[end*i/(nodes-1) for i in range(nodes)];ys0=[math.sin(x) for x in xs]
  if s=='estres' and nodes==5:
   base=[.02,-.03,.02,-.03,.02];perturb=[v*(noise/.03 if noise else 0) for v in base]
  elif s=='normal':perturb=[0.0]*nodes
  else:perturb=[noise*(1 if i%2==0 else -1) for i in range(nodes)]
  ys=[ys0[i]+perturb[i] for i in range(nodes)];domain=(0,end)
  if s=='normal' and nodes==5:test=[math.pi/8,3*math.pi/8,5*math.pi/8,7*math.pi/8]
  elif s=='estres' and nodes==5:test=[math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4]
  elif s=='mal_condicionado':test=[domain[0]+(domain[1]-domain[0])*i/1000 for i in range(1001)]
  else:test=[domain[0]+(domain[1]-domain[0])*(i+.5)/80 for i in range(80) if min(abs(domain[0]+(domain[1]-domain[0])*(i+.5)/80-x) for x in xs)>.02]
 coeff=newton_coeff(xs,ys);base_coeff=newton_coeff(xs,ys0) if ys0 is not None else None
 def funcs_for(yy):
  cc=newton_coeff(xs,yy)
  return [('lagrange','Lagrange',lambda x,yy=yy:lagrange(xs,yy,x)),('newton','Newton por diferencias divididas',lambda x,cc=cc:newton_eval(xs,cc,x)),('spline','Spline cúbico natural',lambda x,yy=yy:spline_natural(xs,yy,x))]
 funcs=funcs_for(ys);basefuncs={code:fn for code,_,fn in funcs_for(ys0)} if ys0 is not None and s=='mal_condicionado' else {}
 out=[];series=[{'name':'Muestras de entrada','data':[[x,y] for x,y in zip(xs,ys)]}]
 if not manual:series.append({'name':'Referencia sin(t)','data':[[domain[0]+(domain[1]-domain[0])*i/200,math.sin(domain[0]+(domain[1]-domain[0])*i/200)] for i in range(201)]})
 errseries=[]
 for code,name,fn in funcs:
  preds=[fn(x) for x in test]
  curve=[[domain[0]+(domain[1]-domain[0])*i/200,fn(domain[0]+(domain[1]-domain[0])*i/200)] for i in range(201)]
  series.append({'name':name,'data':curve})
  if manual:
   spline_fn=next(f for c,_,f in funcs if c=='spline');deviations=[abs(y-spline_fn(x)) for x,y in zip(test,preds)];score=max(deviations) if deviations else 0
   maxerr=None;ref=None;unit='discrepancia entre métodos';rows=[{'n':i+1,'x':x,'prediction':y,'difference_from_spline':d} for i,(x,y,d) in enumerate(zip(test,preds,deviations))]
   errseries.append({'name':name+' vs spline','data':[[x,d] for x,d in zip(test,deviations)]})
  elif s=='mal_condicionado':
   basefn=basefuncs[code];changes=[abs(fn(x)-basefn(x)) for x in test];amplification=(max(changes)/noise) if noise>0 else None
   true_errors=[abs(y-math.sin(x)) for x,y in zip(test,preds)];maxerr=max(true_errors) if true_errors else 0;score=amplification or 0;ref=None;unit='amplificación A';rows=[{'n':i+1,'x':x,'reference':math.sin(x),'prediction':preds[i],'curve_change':changes[i]} for i,x in enumerate(test[::10])]
   # Keep a compact step table; the chart retains all 81 sensitivity samples.
   rows=[]
   for i in range(0,len(test),10):rows.append({'n':i+1,'x':test[i],'reference':math.sin(test[i]),'prediction':preds[i],'curve_change':changes[i]})
   errseries.append({'name':name+' · curva perturbada','data':[[x,d] for x,d in zip(test,changes)]})
  else:
   errs=[y-math.sin(x) for x,y in zip(test,preds)];maxerr=max(abs(e) for e in errs) if errs else 0;score=rmse(errs);ref=0;unit='RMSE';rows=[{'n':i+1,'x':x,'reference':math.sin(x),'approximation':y,'error_abs':abs(y-math.sin(x))} for i,(x,y) in enumerate(zip(test,preds))]
   errseries.append({'name':name,'data':[[x,abs(e)] for x,e in zip(test,errs)]})
  out.append({'code':code,'name':name,'summary_value':score,'unit':unit,'reference_value':ref,'error_abs':maxerr,'error_rel':None,'residual':None,'iterations':len(xs),'steps':rows})
 if manual:
  numeric='Con muestras manuales no hay referencia exacta declarada. Por eso no se reporta error real; la segunda gráfica compara cada interpolante con el spline.'
  applied='La reconstrucción corresponde solo a las muestras ingresadas. Para calcular error real, usa puntos de prueba con valor conocido o la demostración sintética sin(t).'
 elif s=='mal_condicionado':
  ampl=[m['summary_value'] for m in out];numeric=f'El subexperimento mide A=max|pδ(t)-p(t)|/max|δi| en una malla de 1001 puntos; las amplificaciones observadas para Lagrange, Newton y spline son {ampl[0]:.3g}, {ampl[1]:.3g} y {ampl[2]:.3g}. El resultado depende de esta configuración.'
  applied='Se perturban lecturas sintéticas de sin(t) por ±10⁻⁸ en 20 nodos regulares. La amplificación no representa ruido observado en sensores reales.'
 else:
  numeric='Lagrange y Newton representan el mismo interpolante global; el spline cúbico es local por tramos. RMSE y error máximo se calculan en puntos ocultos cuya referencia sin(t) se conoce.'
  applied='Las muestras y perturbaciones son sintéticas. No se utilizan lecturas reales de sensores de Mi Teleférico.'
 return {'case_title':'Reconstrucción de sensores','scenario':s,'parameters':{'nodes':len(xs),'noise':noise,'signal':'muestras manuales' if manual else 'sin(t)','validation_points':len(test),'data_points':raw if manual else None},'methods':out,'charts':[{'title':'Reconstrucción de señal y muestras','x_label':'Tiempo t (rad)' if not manual else 'Coordenada x','y_label':'Lectura','series':series},{'title':'Diferencia entre interpolantes' if manual else ('Cambio de curva ante perturbación' if s=='mal_condicionado' else 'Error absoluto en puntos ocultos'),'x_label':'Tiempo t (rad)' if not manual else 'Coordenada x','y_label':'Diferencia de curva' if manual or s=='mal_condicionado' else 'Error absoluto','series':errseries}],'conclusions':{'numeric':numeric,'case':applied}}
