def trapezoid(f,a,b,n):
 n=max(1,int(n));h=(b-a)/n
 return h*(0.5*f(a)+sum(f(a+i*h) for i in range(1,n))+0.5*f(b))
def simpson(f,a,b,n):
 n=max(2,int(n));n += n%2;h=(b-a)/n
 return h/3*(f(a)+f(b)+4*sum(f(a+i*h) for i in range(1,n,2))+2*sum(f(a+i*h) for i in range(2,n,2)))
def romberg(f,a,b,levels=5):
 rows=[]
 for k in range(levels):
  n=2**k; row=[trapezoid(f,a,b,n)]
  for j in range(1,k+1):row.append(row[j-1]+(row[j-1]-rows[k-1][j-1])/(4**j-1))
  rows.append(row)
 return rows[-1][-1],rows
