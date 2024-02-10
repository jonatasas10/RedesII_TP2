import socket
import os
from dotenv import load_dotenv


load_dotenv()

# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))


def receber_arquivo(nome_arquivo):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', PORTA_UDP))
    dados, endereco_servidor = udp_socket.recvfrom(5242880)

    with open(nome_arquivo, 'wb') as arquivo:
        arquivo.write(dados)
        print(f"Arquivo {nome_arquivo} salvo com sucesso.")
        arquivo.close ()
        udp_socket.close()


# Função para lidar com as mensagens do servidor
def lidar_com_mensagens(cliente_socket):
    try:
        while True:
            mensagem = cliente_socket.recv(5242880).decode()
            print(mensagem)
    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada.")

# Criação do socket TCP do cliente
cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente_socket.connect((HOST, PORTA_TCP))


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

