import socket
import os
import sys
import threading
import time
from dotenv import load_dotenv

from file_transfer_utils import FileTransferServer, FileTransferClient

load_dotenv()

# Configurações do servidor
dir = os.path.dirname(__file__)
files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

server = FileTransferServer()

# Criação do socket TCP do servidor
def main():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind((HOST, PORTA_TCP))
    servidor_socket.listen()

    print(f"Servidor ouvindo em {HOST}:{PORTA_TCP}")
    print(os.getcwd())
    try:

        while True:
            # Aguarda por conexões
            conexao, endereco_cliente = servidor_socket.accept()
            print(f"Conexão estabelecida com {endereco_cliente}")

            # Cria uma thread para lidar com o cliente
            cliente_thread = threading.Thread(target=server.handle_client, args=(conexao, endereco_cliente))
            cliente_thread.start()
            cliente_thread.join()

    except KeyboardInterrupt:
        pass

    servidor_socket.close()

if __name__ == "__main__":
    main()

