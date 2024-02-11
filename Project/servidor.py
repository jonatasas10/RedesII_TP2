import socket
import os
import threading
from dotenv import load_dotenv

load_dotenv()
dir = os.path.dirname(__file__)
files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(files_path)

# Função para enviar um arquivo para o cliente usando UDP
def enviar_arquivo(nome_arquivo, endereco_cliente, porta_cliente):
    try:
        with open(os.path.join(files_path, nome_arquivo), 'rb') as arquivo:
            cliente_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # TODO: Adicionar metodo de envio aqui
            while True:
                dados = arquivo.read(1024)
                if not dados:
                    break
                cliente_udp_socket.sendto(dados, (endereco_cliente, porta_cliente))
                
            cliente_udp_socket.close()
            print(f"Enviado o arquivo {nome_arquivo} para {endereco_cliente}")
    except FileNotFoundError:
        print(f"Arquivo {nome_arquivo} não encontrado no servidor.")

# Função para lidar com as solicitações de um cliente
def lidar_com_cliente(conexao, endereco_cliente):
    try:
        # Envia a lista de arquivos para o cliente
        arquivos_disponiveis = listar_arquivos()
        mensagem_inicial = "\n".join(arquivos_disponiveis)
        conexao.sendall(mensagem_inicial.encode())

        # Loop para lidar com as solicitações do cliente
        while True:
            # Recebe a solicitação do cliente para download usando UDP
            nome_arquivo = conexao.recv(4096).decode()

            if not nome_arquivo:
                break  # Cliente encerrou a conexão

            # Envia o arquivo usando UDP
            enviar_arquivo(nome_arquivo, endereco_cliente[0], PORTA_UDP)
            
    except ConnectionResetError:
        print(f"Conexão com {endereco_cliente} foi encerrada pelo cliente.")

    finally:
        # Fecha a conexão TCP
        conexao.close()

# Configurações do servidor
""" HOST = '127.0.0.1'
PORTA_TCP = 12345
PORTA_UDP = 54321 """

# Criação do socket TCP do servidor
servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor_socket.bind((HOST, PORTA_TCP))
servidor_socket.listen()

print(f"Servidor ouvindo em {HOST}:{PORTA_TCP}")
print(os.getcwd())
while True:
    # Aguarda por conexões
    conexao, endereco_cliente = servidor_socket.accept()
    print(f"Conexão estabelecida com {endereco_cliente}")

    # Cria uma thread para lidar com o cliente
    cliente_thread = threading.Thread(target=lidar_com_cliente, args=(conexao, endereco_cliente))
    cliente_thread.start()
