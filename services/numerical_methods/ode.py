def rk2_system(f,t0,y0,h,n):
 t=t0;y=list(y0);rows=[{'n':0,'t':t,'y':y[:]}]
 for i in range(1,n+1):
  k1=f(t,y);ym=[y[j]+h*k1[j]/2 for j in range(len(y))];k2=f(t+h/2,ym)
  y=[y[j]+h*k2[j] for j in range(len(y))];t=t0+i*h;rows.append({'n':i,'t':t,'y':y[:]})
 return rows
def rk4_system(f,t0,y0,h,n):
 t=t0;y=list(y0);rows=[{'n':0,'t':t,'y':y[:]}]
 for i in range(1,n+1):
  k1=f(t,y);k2=f(t+h/2,[y[j]+h*k1[j]/2 for j in range(len(y))]);k3=f(t+h/2,[y[j]+h*k2[j]/2 for j in range(len(y))]);k4=f(t+h,[y[j]+h*k3[j] for j in range(len(y))])
  y=[y[j]+h*(k1[j]+2*k2[j]+2*k3[j]+k4[j])/6 for j in range(len(y))];t=t0+i*h;rows.append({'n':i,'t':t,'y':y[:]})
 return rows
