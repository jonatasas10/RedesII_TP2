import random
import socket
import os
import time
from dotenv import load_dotenv


load_dotenv()

# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))


def receber_arquivo(nome_arquivo, wa):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', PORTA_UDP))
    dados, endereco_servidor = udp_socket.recvfrom(5242880)

    with open(nome_arquivo, 'wb') as arquivo:
        arquivo.write(dados)
        print(f"Arquivo {nome_arquivo} salvo com sucesso.")
        arquivo.close ()
        udp_socket.close()

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

# Função para lidar com as mensagens do servidor
def lidar_com_mensagens(cliente_socket):
    try:
        while True:
            mensagem = cliente_socket.recv(5242880).decode()
            print(mensagem)
    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada.")

def simulate_network_delay():
    random_delay = random.uniform(0, 0.5)
    time.sleep(random_delay)


# Criação do socket TCP do cliente
cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente_socket.connect((HOST, PORTA_TCP))

#Dummy code
data = b"Hello, server!"
cliente_socket.sendall(data)

# Recebe a lista de arquivos do servidor
arquivos_disponiveis = cliente_socket.recv(4096).decode()


# Inicia a thread para lidar com mensagens do servidor
# thread_mensagens = threading.Thread(target=lidar_com_mensagens, args=(cliente_socket,))
# thread_mensagens.start()

try:

    while True:

            # Recebe a lista de arquivos do servidor # aqui estava dando erro logo aops recebimento, passou para cima.
            # arquivos_disponiveis = cliente_socket.recv(4096).decode()  # o recv() nao precisa ser deste tamanho, pode ser menor '4096'.
            
            print("Arquivos disponíveis para download:")
            print(arquivos_disponiveis)

            # Solicitação do cliente para download usando UDP
            nome_arquivo = input("Digite o nome do arquivo que deseja baixar (ou 'sair' para encerrar): ")

            if nome_arquivo.lower() == 'sair':
                cliente_socket.sendall(nome_arquivo.encode())
                # cliente_socket.close()
                break

            cliente_socket.sendall(nome_arquivo.encode())
            receber_arquivo(nome_arquivo)
            
           
except KeyboardInterrupt:
    pass


# # Fecha a conexão TCP
cliente_socket.close()

