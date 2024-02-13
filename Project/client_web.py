import random
import socket
import os
import time
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

app = Flask(__name__)


def receber_arquivo(nome_arquivo):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', PORTA_UDP))
    udp_socket.settimeout(5)
    expected_sequence_number = 0

    with open(nome_arquivo, 'wb') as arquivo:
        while True:
            try:
                packet, address = udp_socket.recvfrom(1024*8)
                sequence_number_bytes = packet[:4]  # Extrai apenas os 4 primeiros bytes
                sequence_number = int.from_bytes(sequence_number_bytes, byteorder='big')
                
                print(f"recebido {sequence_number} {expected_sequence_number}")
                if sequence_number == expected_sequence_number:
                    arquivo.write(packet[4:])
                    ack = str(sequence_number+1)
                    udp_socket.sendto(ack.encode(), address)
                    expected_sequence_number += 1
            except socket.timeout:
                print("Timeout. Conexão encerrada.")
                break

    print(f"Arquivo {nome_arquivo} recebido com sucesso.")
    ack = str(-1)
    udp_socket.sendto(ack.encode(), address)

    udp_socket.close()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/file_list', methods=['GET'])
def get_file_list():
    #files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
    #file_list = os.listdir(files_path)

    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect((HOST, PORTA_TCP))

    #Dummy code
    data = b"Hello, server!"
    cliente_socket.sendall(data)

    # Recebe a lista de arquivos do servidor
    arquivos_disponiveis = cliente_socket.recv(4096).decode().split("\n")
    cliente_socket.close()
    return jsonify(arquivos_disponiveis)

@app.route('/download', methods=['POST'])
def download():
    file_name = request.form['file_name']
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect((HOST, PORTA_TCP))

    data = b"Hello, server!"
    cliente_socket.sendall(data)

    # Recebe a lista de arquivos do servidor
    arquivos_disponiveis = cliente_socket.recv(4096).decode().split("\n")

    cliente_socket.sendall(file_name.encode())
    receber_arquivo(file_name)

    cliente_socket.close()

    return f'Arquivo {file_name} recebido com sucesso.'


if __name__ == '__main__':
    app.run(debug=True)
