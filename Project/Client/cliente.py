import socket, select, traceback, queue
import os
from dotenv import load_dotenv
from time import sleep, time
from numpy import random
import zlib
from flask import Flask, jsonify, redirect, request, render_template, url_for
import threading
from client_server_utils import enviar_arquivo, receber_arquivo, listar_arquivos



load_dotenv()

app = Flask(__name__)
# Configurações do cliente
dir = os.path.dirname(__file__)
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))
client_files_path = os.path.join(dir, os.environ.get("CLIENT_FILES_PATH"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/file_list', methods=['GET'])
def get_file_list():
    global arquivos_disponiveis
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    operacao = f"listar _"
    cliente_socket.sendto(operacao.encode(), (HOST, PORTA_UDP))
    # Recebe a lista de arquivos do servidor
    arquivos_disponiveis = cliente_socket.recv(4096).decode().split("\n")

    cliente_socket.close()
    return jsonify(arquivos_disponiveis)

@app.route('/download', methods=['POST'])
def download():
    file_name = request.form['file_name']
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    if file_name not in arquivos_disponiveis:
        operacao = f"nofile  "
        cliente_socket.sendto(operacao.encode(), (HOST, PORTA_UDP))
        cliente_socket.close()
        print(f'Arquivo {file_name} inexistente no servidor.')
        return f'Arquivo {file_name} inexistente no servidor.'

    operacao = f"download {file_name}"
    cliente_socket.sendto(operacao.encode(), (HOST, PORTA_UDP))

    receber_arquivo(cliente_socket, file_name)

    cliente_socket.close()
    return f'Arquivo {file_name} recebido com sucesso.'


# Upload de arquivos
@app.route('/upload_page')
def upload_page():
    return render_template('upload.html')

@app.route('/client_file_list', methods=['GET'])
def get_client_file_list():
    arquivos_para_upload = os.listdir(client_files_path)
    return jsonify(arquivos_para_upload)

@app.route('/upload', methods=['POST'])
def upload():
    upload_file_name = request.form['upload_file_name']
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if upload_file_name not in listar_arquivos():
        operacao = f"nofile  "
        cliente_socket.sendto(operacao.encode(), (HOST, PORTA_UDP))
        cliente_socket.close()
        print(f'Arquivo {upload_file_name} inexistente no cliente.')
        return f'Arquivo {upload_file_name} inexistente no cliente.'

    operacao = f"upload {upload_file_name}"
    cliente_socket.sendto(operacao.encode(), (HOST, PORTA_UDP))

    enviar_arquivo(upload_file_name, (HOST, PORTA_UDP), cliente_socket)

    cliente_socket.close()
    return f'Arquivo {upload_file_name} enviado com sucesso.'

@app.route('/auth_page')
def auth_page():
    return render_template('auth.html')

@app.route('/auth', methods=['POST'])
def auth():
    usuario = request.form['user']
    senha = request.form['password']

    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    auth = f"{usuario}|{senha}"
    operacao = f"auth {auth}"
    cliente_socket.sendto(operacao.encode(), (HOST, PORTA_UDP))

    resposta = cliente_socket.recv(4096).decode()
    cliente_socket.close()

    if resposta == "ok":
        return render_template('upload.html')
    else:
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()