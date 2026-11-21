"""SQLite persistence for reproducible simulations and their numerical output."""
import json,sqlite3
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
CASES={'detencion':'M1 · Detención de emergencia','deterioro':'M2 · Deterioro y mantenimiento','oscilaciones':'M3 · Oscilaciones por viento','sensores':'M4 · Reconstrucción de sensores'}
SCENARIOS={'normal':'Normal','estres':'Estrés','mal_condicionado':'Mal condicionado'}
@contextmanager
def connect(path):
 c=sqlite3.connect(path,timeout=20);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=20000')
 try:
  with c:yield c
 finally:c.close()
def initialize(path):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 with connect(path) as c:
  c.execute('PRAGMA journal_mode=WAL')
  c.executescript("""
  CREATE TABLE IF NOT EXISTS caso_estudio(id INTEGER PRIMARY KEY AUTOINCREMENT,codigo TEXT NOT NULL UNIQUE,nombre TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS escenario(id INTEGER PRIMARY KEY AUTOINCREMENT,caso_id INTEGER NOT NULL REFERENCES caso_estudio(id),codigo TEXT NOT NULL,nombre TEXT NOT NULL,descripcion TEXT NOT NULL,UNIQUE(caso_id,codigo));
  CREATE TABLE IF NOT EXISTS simulacion(id INTEGER PRIMARY KEY AUTOINCREMENT,escenario_id INTEGER NOT NULL REFERENCES escenario(id),fecha TEXT NOT NULL,estado TEXT NOT NULL,parameters_json TEXT NOT NULL,result_json TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS ejecucion_metodo(id INTEGER PRIMARY KEY AUTOINCREMENT,simulacion_id INTEGER NOT NULL REFERENCES simulacion(id) ON DELETE CASCADE,method_code TEXT NOT NULL,method_name TEXT NOT NULL,status TEXT NOT NULL,result_json TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS iteracion_resultado(id INTEGER PRIMARY KEY AUTOINCREMENT,ejecucion_id INTEGER NOT NULL REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,numero INTEGER NOT NULL,datos_json TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS resultado_resumen(id INTEGER PRIMARY KEY AUTOINCREMENT,simulacion_id INTEGER NOT NULL UNIQUE REFERENCES simulacion(id) ON DELETE CASCADE,datos_json TEXT NOT NULL);
  CREATE INDEX IF NOT EXISTS idx_sim_fecha ON simulacion(fecha DESC);
  CREATE INDEX IF NOT EXISTS idx_exec_sim ON ejecucion_metodo(simulacion_id);
  CREATE INDEX IF NOT EXISTS idx_iter_exec ON iteracion_resultado(ejecucion_id,numero);
  """)
  for code,name in CASES.items():
   c.execute('INSERT OR IGNORE INTO caso_estudio(codigo,nombre) VALUES(?,?)',(code,name));case_id=c.execute('SELECT id FROM caso_estudio WHERE codigo=?',(code,)).fetchone()['id']
   for sc,label in SCENARIOS.items():c.execute('INSERT OR IGNORE INTO escenario(caso_id,codigo,nombre,descripcion) VALUES(?,?,?,?)',(case_id,sc,label,'Escenario académico con parámetros sintéticos.'))
def ping(path):
 with connect(path) as c:c.execute('SELECT 1').fetchone()
def catalog():return [{'code':c,'name':n} for c,n in CASES.items()]
def save_run(path,req,result):
 code=req.get('case');scenario=req.get('scenario','normal')
 if code not in CASES:raise ValueError('Seleccione uno de los cuatro módulos.')
 if scenario not in SCENARIOS:raise ValueError('Seleccione un escenario válido.')
 stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
 with connect(path) as c:
  sid=c.execute('SELECT e.id FROM escenario e JOIN caso_estudio k ON k.id=e.caso_id WHERE k.codigo=? AND e.codigo=?',(code,scenario)).fetchone()['id']
  cur=c.execute('INSERT INTO simulacion(escenario_id,fecha,estado,parameters_json,result_json) VALUES(?,?,?,?,?)',(sid,stamp,'completada',json.dumps(req.get('parameters',{}),ensure_ascii=False,allow_nan=False),'{}'));rid=cur.lastrowid
  for m in result.get('methods',[]):
   ec=c.execute('INSERT INTO ejecucion_metodo(simulacion_id,method_code,method_name,status,result_json) VALUES(?,?,?,?,?)',(rid,m.get('code',''),m.get('name',''),m.get('status','completada'),json.dumps(m,ensure_ascii=False,allow_nan=False))).lastrowid
   c.executemany('INSERT INTO iteracion_resultado(ejecucion_id,numero,datos_json) VALUES(?,?,?)',[(ec,i+1,json.dumps(step,ensure_ascii=False,allow_nan=False)) for i,step in enumerate(m.get('steps',[]))])
  c.execute('INSERT INTO resultado_resumen(simulacion_id,datos_json) VALUES(?,?)',(rid,json.dumps({'charts':result.get('charts',[]),'conclusions':result.get('conclusions',{}),'parameters':result.get('parameters',{})},ensure_ascii=False,allow_nan=False)))
  result['simulation_id']=rid;c.execute('UPDATE simulacion SET result_json=? WHERE id=?',(json.dumps(result,ensure_ascii=False,allow_nan=False),rid))
 return rid
def history(path,code=None):
 q='SELECT s.id,k.codigo AS case_code,k.nombre AS case_name,e.codigo AS scenario,e.nombre AS scenario_name,s.fecha AS created_at,s.estado AS status FROM simulacion s JOIN escenario e ON e.id=s.escenario_id JOIN caso_estudio k ON k.id=e.caso_id';args=()
 if code:q+=' WHERE k.codigo=?';args=(code,)
 q+=' ORDER BY s.id DESC LIMIT 100'
 with connect(path) as c:return [dict(x) for x in c.execute(q,args).fetchall()]
def get_run(path,rid):
 with connect(path) as c:r=c.execute('SELECT s.*,k.codigo AS case_code,k.nombre AS case_name,e.codigo AS scenario,e.nombre AS scenario_name FROM simulacion s JOIN escenario e ON e.id=s.escenario_id JOIN caso_estudio k ON k.id=e.caso_id WHERE s.id=?',(rid,)).fetchone()
 if r is None:return None
 d=dict(r);d['parameters']=json.loads(d.pop('parameters_json'));d['result']=json.loads(d.pop('result_json'));return d

def delete_run(path,rid):
 """Delete one saved simulation; dependent method, iteration and summary rows cascade."""
 with connect(path) as c:
  cur=c.execute('DELETE FROM simulacion WHERE id=?',(rid,))
  return cur.rowcount>0
