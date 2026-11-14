def bisection(f,a,b,tol=1e-8,max_iter=200):
 fa,fb=f(a),f(b)
 if fa*fb>0:raise ValueError('Bisección necesita un intervalo con cambio de signo.')
 rows=[]
 for i in range(1,max_iter+1):
  c=(a+b)/2;fc=f(c);rows.append({'n':i,'x':c,'fx':fc,'error':(b-a)/2})
  if abs(fc)<=tol or (b-a)/2<=tol:break
  if fa*fc<=0:b,fb=c,fc
  else:a,fa=c,fc
 return rows[-1]['x'],rows
def newton(f,df,x,tol=1e-8,max_iter=100):
 rows=[]
 for i in range(1,max_iter+1):
  fx=f(x);d=df(x)
  if abs(d)<1e-14:break
  nxt=x-fx/d;rows.append({'n':i,'x':nxt,'fx':f(nxt),'error':abs(nxt-x)})
  if abs(nxt-x)<=tol or abs(f(nxt))<=tol:x=nxt;break
  x=nxt
 if not rows:raise ValueError('Newton no pudo avanzar: derivada nula o demasiado pequeña.')
 return rows[-1]['x'],rows
def secant(f,x0,x1,tol=1e-8,max_iter=100):
 rows=[]
 for i in range(1,max_iter+1):
  f0,f1=f(x0),f(x1);den=f1-f0
  if abs(den)<1e-15:break
  x2=x1-f1*(x1-x0)/den;rows.append({'n':i,'x':x2,'fx':f(x2),'error':abs(x2-x1)})
  if abs(x2-x1)<=tol or abs(f(x2))<=tol:x1=x2;break
  x0,x1=x1,x2
 if not rows:raise ValueError('Secante no pudo avanzar con las semillas seleccionadas.')
 return rows[-1]['x'],rows
