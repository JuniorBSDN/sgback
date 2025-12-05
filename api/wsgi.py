"""
Ponto de entrada padrão para o protocolo WSGI.
Servidores web (como Gunicorn, Apache com mod_wsgi, Vercel)
irão procurar pela variável 'application'.
"""
from app import app as application
