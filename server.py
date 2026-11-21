"""Servidor local; PythonAnywhere importa wsgi.application."""
import argparse,threading,webbrowser
from wsgiref.simple_server import make_server
from app import application
def main():
 p=argparse.ArgumentParser(description='SIMTELE-RISK local');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8000);p.add_argument('--open-browser',action='store_true');a=p.parse_args()
 if not 1<=a.port<=65535:p.error('El puerto debe estar entre 1 y 65535.')
 url=f'http://{a.host}:{a.port}'
 try:httpd=make_server(a.host,a.port,application)
 except OSError as e:print(f'No se pudo abrir el puerto {a.port}: {e}');return 1
 print(f'SIMTELE-RISK disponible en {url}. Ctrl+C detiene el servidor.',flush=True)
 if a.open_browser:
  t=threading.Timer(.5,webbrowser.open,args=(url,));t.daemon=True;t.start()
 try:httpd.serve_forever()
 except KeyboardInterrupt:print('\nServidor detenido; el historial permanece guardado.')
 finally:httpd.server_close()
 return 0
if __name__=='__main__':raise SystemExit(main())
