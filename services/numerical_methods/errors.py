import math
def errors(value,reference,residual=None):
 absolute=abs(value-reference) if value is not None and reference is not None else None
 relative=(absolute/abs(reference)) if absolute is not None and abs(reference)>1e-15 else None
 return {'absolute':absolute,'relative':relative,'percent':100*relative if relative is not None else None,'residual':abs(residual) if residual is not None else None}
def rmse(values):return math.sqrt(sum(v*v for v in values)/len(values)) if values else 0.0
