import random
import socket
import os
import time
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from file_transfer_utils import FileTransferServer, FileTransferClient


load_dotenv()

# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

app = Flask(__name__)
client = FileTransferClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/file_list', methods=['GET'])
def get_file_list():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect((HOST, PORTA_TCP))


    # Recebe a lista de arquivos do servidor
    arquivos_disponiveis = cliente_socket.recv(4096).decode().split("\n")
    cliente_socket.close()
    return jsonify(arquivos_disponiveis)

@app.route('/download', methods=['POST'])
def download():
    file_name = request.form['file_name']
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect((HOST, PORTA_TCP))

    # Recebe a lista de arquivos do servidor
    arquivos_disponiveis = cliente_socket.recv(4096).decode().split("\n")

    cliente_socket.sendall(file_name.encode())
    client.receber_arquivo(file_name)

    cliente_socket.close()

    return f'Arquivo {file_name} recebido com sucesso.'


if __name__ == '__main__':
    app.run(debug=True)
