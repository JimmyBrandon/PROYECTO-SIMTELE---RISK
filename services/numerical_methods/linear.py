import math
def residual(A,x,b):return math.sqrt(sum((sum(A[i][j]*x[j] for j in range(len(x)))-b[i])**2 for i in range(len(x))))
def jacobi(A,b,x0=None,tol=1e-10,max_iter=500):
 n=len(b);x=list(x0 or [0.0]*n);rows=[]
 for k in range(1,max_iter+1):
  y=[(b[i]-sum(A[i][j]*x[j] for j in range(n) if j!=i))/A[i][i] for i in range(n)];r=residual(A,y,b);rows.append({'n':k,'x':y[:],'residual':r})
  if r<=tol:x=y;break
  x=y
 return x,rows
def gauss_seidel(A,b,x0=None,tol=1e-10,max_iter=500):
 n=len(b);x=list(x0 or [0.0]*n);rows=[]
 for k in range(1,max_iter+1):
  y=x[:]
  for i in range(n):y[i]=(b[i]-sum(A[i][j]*y[j] for j in range(n) if j!=i))/A[i][i]
  r=residual(A,y,b);rows.append({'n':k,'x':y[:],'residual':r})
  if r<=tol:x=y;break
  x=y
 return x,rows
def lu_solve(A,b):
 n=len(b);M=[list(map(float,row))+[float(b[i])] for i,row in enumerate(A)]
 for k in range(n):
  p=max(range(k,n),key=lambda i:abs(M[i][k]))
  if abs(M[p][k])<1e-14:raise ValueError('La matriz del sistema es singular.')
  M[k],M[p]=M[p],M[k]
  for i in range(k+1,n):
   q=M[i][k]/M[k][k]
   for j in range(k,n+1):M[i][j]-=q*M[k][j]
 x=[0.0]*n
 for i in range(n-1,-1,-1):x[i]=(M[i][n]-sum(M[i][j]*x[j] for j in range(i+1,n)))/M[i][i]
 return x

def conjugate_gradient(A,b,tol=1e-10,max_iter=500):
 n=len(b);x=[0.0]*n;r=[b[i] for i in range(n)];p=r[:];rs=sum(v*v for v in r);rows=[]
 for k in range(1,max_iter+1):
  Ap=[sum(A[i][j]*p[j] for j in range(n)) for i in range(n)];den=sum(p[i]*Ap[i] for i in range(n))
  if den<=0:raise ValueError('Gradiente conjugado requiere una matriz SPD.')
  alpha=rs/den;x=[x[i]+alpha*p[i] for i in range(n)];r=[r[i]-alpha*Ap[i] for i in range(n)];new=sum(v*v for v in r);rows.append({'n':k,'x':x[:],'residual':math.sqrt(new)})
  if math.sqrt(new)<=tol:break
  p=[r[i]+(new/rs)*p[i] for i in range(n)];rs=new
 return x,rows

def condition_inf(A):
 n=len(A);cols=[]
 for j in range(n):
  e=[0.0]*n;e[j]=1.0;cols.append(lu_solve(A,e))
 inv=[[cols[j][i] for j in range(n)] for i in range(n)]
 norm_a=max(sum(abs(v) for v in row) for row in A)
 norm_i=max(sum(abs(v) for v in row) for row in inv)
 return norm_a*norm_i
