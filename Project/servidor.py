import socket, select, traceback
import os
import threading
import pickle
from dotenv import load_dotenv
from time import time
import PyPDF2
load_dotenv()
dir = os.path.dirname(__file__)
files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

ACK = 0

# Configurações do servidor
""" HOST = '127.0.0.1'
PORTA_TCP = 12345
PORTA_UDP = 54321 """

def receber_ack(servidor_socket):
    global ACK
    servidor_socket.setblocking(False)
    ler_socket, _, _ = select.select([servidor_socket], [], [], 0.0)
    for s in ler_socket:
        if s is servidor_socket:
            dados, _ = servidor_socket.recvfrom(100)
            ACK = int(dados.decode('utf8'))
            print("ACK recebido", ACK)

# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(files_path)

# Função para enviar um arquivo para o cliente usando UDP
def enviar_arquivo(nome_arquivo, endereco_cliente, servidor_socket):
    try:
        with open(os.path.join(files_path, nome_arquivo), 'rb') as arquivo:


            global ACK
            sequencia_base = 0
            proximo_numero_sequencia = 0
            arquivo.seek(sequencia_base)
            N = 4
            timeout = []
            tempo = []

            while True:
                dados = arquivo.read(1024//10)

                if not dados and ACK == proximo_numero_sequencia -1:
                    print("Fim do arquivo, ACK =", ACK)

                    break
                if proximo_numero_sequencia < sequencia_base + N and dados:
                    tempo.append(time())
                    servidor_socket.sendto(dados, endereco_cliente)
                    print("Número de sequência enviado:", proximo_numero_sequencia)
                    servidor_socket.sendto(str(proximo_numero_sequencia).encode(), endereco_cliente)
                    # Para receber um ack
                    threading.Thread(target=receber_ack, args=[servidor_socket]).start()
                    proximo_numero_sequencia += 1
                else:
                    servidor_socket.setblocking(True)
                    dados_ack, _ = servidor_socket.recvfrom(100)
                    print("Ultimos ACKS após enviar todo pacote:", dados_ack.decode())
                    ACK = int(dados_ack.decode())

                    #threading.Thread(target=receber_ack, args=[servidor_socket]).start()

                sequencia_base += 1

            servidor_socket.sendto('eof'.encode(), endereco_cliente)
            print(f"Enviado o arquivo {nome_arquivo} para {endereco_cliente}")

    except FileNotFoundError:
        print(f"Arquivo {nome_arquivo} não encontrado no servidor.")
    except Exception as e:
        print("algum erro", e)
        traceback.print_exc()

# Função para lidar com as solicitações de um cliente
def lidar_com_cliente(servidor_socket, endereco_cliente):

    try:
        # Envia a lista de arquivos para o cliente
        arquivos_disponiveis = listar_arquivos()
        mensagem_inicial = "\n".join(arquivos_disponiveis)

        servidor_socket.sendto(mensagem_inicial.encode(), endereco_cliente)

        nome_arquivo, _ = servidor_socket.recvfrom(1024)

        nome_arquivo = nome_arquivo.decode()
        print(nome_arquivo, endereco_cliente)
        # Envia o arquivo usando UDP
        enviar_arquivo(nome_arquivo, endereco_cliente, servidor_socket)

    except ConnectionResetError:
        print(f"Conexão com {endereco_cliente} foi encerrada pelo cliente.")

    finally:
        return nome_arquivo


def main():
    try:
        servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        servidor_socket.bind((HOST, PORTA_UDP))
        while True:
            #print(f"Servidor ouvindo em {HOST}:{PORTA_UDP}")
            mensagem, endereco_cliente = servidor_socket.recvfrom(1024)
            lidar_com_cliente(servidor_socket, endereco_cliente)

    except KeyboardInterrupt:
        print("\nEncerrando socket do servidor.")
        servidor_socket.close()
    finally:
        servidor_socket.close()

if __name__ == "__main__":
    main()
