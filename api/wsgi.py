"""
Ponto de entrada padrão para o protocolo WSGI.
Servidores web (como Gunicorn, Apache com mod_wsgi, Vercel)
irão procurar pela variável 'application'.
"""
from app import app as application


if __name__ == "__main__":
    # Permite rodar diretamente com `python wsgi.py` em desenvolvimento,
    # embora o comando `flask run` ou `python app.py` seja mais comum.
    application.run()