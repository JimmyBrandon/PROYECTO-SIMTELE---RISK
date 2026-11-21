def lagrange(xs,ys,x):
 total=0.0
 for i,xi in enumerate(xs):
  term=ys[i]
  for j,xj in enumerate(xs):
   if j!=i:term*= (x-xj)/(xi-xj)
  total+=term
 return total
def newton_coeff(xs,ys):
 c=list(ys)
 for j in range(1,len(xs)):
  for i in range(len(xs)-1,j-1,-1):c[i]=(c[i]-c[i-1])/(xs[i]-xs[i-j])
 return c
def newton_eval(xs,c,x):
 v=c[-1]
 for i in range(len(c)-2,-1,-1):v=c[i]+(x-xs[i])*v
 return v
def spline_natural(xs,ys,x):
 n=len(xs);h=[xs[i+1]-xs[i] for i in range(n-1)]
 if x<=xs[0]:i=0
 elif x>=xs[-1]:i=n-2
 else:i=next(j for j in range(n-1) if xs[j]<=x<=xs[j+1])
 # Solve natural cubic second derivatives with a tridiagonal system.
 m=[0.0]*n
 if n>2:
  size=n-2;A=[[0.0]*size for _ in range(size)];b=[0.0]*size
  for r in range(size):
   k=r+1;A[r][r]=2*(h[k-1]+h[k])
   if r>0:A[r][r-1]=h[k-1]
   if r<size-1:A[r][r+1]=h[k]
   b[r]=6*((ys[k+1]-ys[k])/h[k]-(ys[k]-ys[k-1])/h[k-1])
  for k in range(size):
   piv=A[k][k]
   if abs(piv)<1e-15:raise ValueError('Sistema del spline singular.')
   for j in range(k+1,size):
    q=A[j][k]/piv
    for z in range(k,size):A[j][z]-=q*A[k][z]
    b[j]-=q*b[k]
  sol=[0.0]*size
  for k in range(size-1,-1,-1):sol[k]=(b[k]-sum(A[k][j]*sol[j] for j in range(k+1,size)))/A[k][k]
  m[1:-1]=sol
 hi=xs[i+1]-x;lo=x-xs[i]
 return m[i]*hi**3/(6*h[i])+m[i+1]*lo**3/(6*h[i])+ (ys[i]-m[i]*h[i]**2/6)*hi/h[i]+(ys[i+1]-m[i+1]*h[i]**2/6)*lo/h[i]
