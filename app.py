"""SIMTELE-RISK WSGI application."""
import json, logging, os
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import storage
from services.case_modules import run_case, catalog as case_catalog
ROOT=Path(__file__).resolve().parent
WEB=ROOT/'web'
MAX_BODY=200_000
STATIC={'/':('index.html','text/html; charset=utf-8'),'/app.js':('static/app.js','text/javascript; charset=utf-8'),'/style.css':('static/style.css','text/css; charset=utf-8'),'/controls.css':('static/controls.css','text/css; charset=utf-8'),'/theme.css':('static/theme.css','text/css; charset=utf-8'),'/favicon.svg':('static/favicon.svg','image/svg+xml')}
class RequestError(Exception):
 def __init__(self,message,status=400): super().__init__(message); self.status=status
def db_path():
 p=Path(os.environ.get('SIMTELE_DB','').strip() or ROOT/'instance'/'simtele_risk.sqlite3').expanduser()
 if not p.is_absolute(): p=ROOT/p
 p.parent.mkdir(parents=True,exist_ok=True)
 return p.resolve()
DB=db_path(); storage.initialize(DB)
def read_json(env):
 if env.get('CONTENT_TYPE','').split(';',1)[0].strip().lower()!='application/json': raise RequestError('La solicitud debe usar application/json.',415)
 try:n=int(env.get('CONTENT_LENGTH') or 0)
 except ValueError:raise RequestError('Longitud de solicitud inválida.')
 if n<=0 or n>MAX_BODY:raise RequestError('Tamaño de solicitud no válido.',413)
 try:data=json.loads(env['wsgi.input'].read(n).decode('utf-8'))
 except (ValueError,UnicodeError):raise RequestError('El contenido JSON no es válido.')
 if not isinstance(data,dict):raise RequestError('Se esperaba un objeto JSON.')
 return data
def respond(start,status,body,kind='application/json; charset=utf-8',head=False):
 payload=(json.dumps(body,ensure_ascii=False,allow_nan=False).encode('utf-8') if kind.startswith('application/json') else body)
 headers=[('Content-Type',kind),('Content-Length',str(len(payload))),('X-Content-Type-Options','nosniff'),('X-Frame-Options','SAMEORIGIN'),('Cache-Control','no-store')]
 start(f'{status} {HTTPStatus(status).phrase}',headers)
 return [] if head or status==204 else [payload]
def application(env,start):
 method=env.get('REQUEST_METHOD','GET').upper(); path=env.get('PATH_INFO') or '/'
 try:
  if method in ('GET','HEAD'):
   if path in STATIC:
    rel,kind=STATIC[path]; target=WEB/rel
    if not target.is_file(): raise RequestError('No encontrado.',404)
    return respond(start,200,target.read_bytes(),kind,method=='HEAD')
   if path=='/api/catalog':return respond(start,200,case_catalog())
   if path=='/api/history':return respond(start,200,storage.history(DB,parse_qs(env.get('QUERY_STRING','')).get('case',[None])[0]))
   if path.startswith('/api/history/'):
    tail=path.rsplit('/',1)[-1]
    if not tail.isdigit():raise RequestError('Identificador no válido.')
    item=storage.get_run(DB,int(tail))
    if item is None:raise RequestError('La simulación no existe.',404)
    return respond(start,200,item)
   if path=='/health':storage.ping(DB);return respond(start,200,{'status':'ok','database':'sqlite'})
   if path=='/favicon.ico':return respond(start,204,b'','image/x-icon')
   raise RequestError('Ruta no encontrada.',404)
  if method=='DELETE' and path.startswith('/api/history/'):
   origin=env.get('HTTP_ORIGIN')
   if origin and urlsplit(origin).netloc.lower()!=env.get('HTTP_HOST','').lower():raise RequestError('Solicitud de origen no permitido.',403)
   tail=path.rsplit('/',1)[-1]
   if not tail.isdigit():raise RequestError('Identificador no válido.')
   rid=int(tail)
   if not storage.delete_run(DB,rid):raise RequestError('La simulación ya no existe.',404)
   return respond(start,200,{'deleted':True,'id':rid})
  if method!='POST':raise RequestError('Método no permitido.',405)
  origin=env.get('HTTP_ORIGIN')
  if origin and urlsplit(origin).netloc.lower()!=env.get('HTTP_HOST','').lower():raise RequestError('Solicitud de origen no permitido.',403)
  if path in ('/api/execute','/api/rerun'):
   req=read_json(env); result=run_case(req); result['simulation_id']=storage.save_run(DB,req,result)
   return respond(start,201,result)
  raise RequestError('Ruta no encontrada.',404)
 except RequestError as e:return respond(start,e.status,{'error':str(e)})
 except (ValueError,TypeError,OverflowError,ZeroDivisionError) as e:return respond(start,400,{'error':str(e) or 'Parámetros no válidos.'})
 except Exception:
  logging.exception('Error interno SIMTELE-RISK')
  return respond(start,500,{'error':'No se pudo completar el cálculo. Revisa los parámetros e inténtalo nuevamente.'})
