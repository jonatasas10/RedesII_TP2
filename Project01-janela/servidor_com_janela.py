import socket
import os
import threading
from dotenv import load_dotenv

import time

load_dotenv()
dir = os.path.dirname(__file__)
files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(files_path)

def enviar_pacote(dados, endereco_cliente, porta_cliente, sequencia):
    pacote = f"{sequencia}:{dados}"
    cliente_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cliente_udp_socket.sendto(pacote.encode(), (endereco_cliente, porta_cliente))
    cliente_udp_socket.close()
# Função para enviar uma janela de pacotes
def enviar_janela(janela, endereco_cliente, porta_cliente):
    for i, dados in enumerate(janela):
        enviar_pacote(dados, endereco_cliente, porta_cliente, i)


# Função para enviar um arquivo para o cliente usando UDP
def enviar_arquivo(nome_arquivo, endereco_cliente, porta_cliente):
    try:
        with open(os.path.join(files_path, nome_arquivo), 'rb') as arquivo:
            cliente_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dados = arquivo.read(1024)
            tamanho_janela = 3     
    # TODO: Adicionar metodo de envio aqui
            # while True:
            for i in range(0, len(dados), tamanho_janela):
                # dados = arquivo.read(786432)
                janela = dados[i:i+tamanho_janela]
                enviar_janela(janela, endereco_cliente, porta_cliente)
                time.sleep(1.1)  # Simula o tempo de transmissão
                
                # Envia um pacote de confirmação indicando o fim do arquivo
                enviar_pacote("EOF", endereco_cliente, porta_cliente, -1)
                
                print(f"Arquivo {nome_arquivo} enviado para {endereco_cliente}")
                
                # if not dados:
                #     break
            # Cliente_udp_socket.sendto(dados, (endereco_cliente, porta_cliente))
            cliente_udp_socket.close()
            # print(f"Enviado o arquivo {nome_arquivo} para {endereco_cliente}")
    
    except FileNotFoundError:

        if nome_arquivo == 'sair':
            print('Cliente desconectou-se...')
        else:    
            print(f"Arquivo {nome_arquivo} não encontrado no servidor.")

def autenticar_cliente(conexao):
    senha_correta = "123"  # Substitua pela senha desejada

    conexao.sendall("Digite a senha para autenticação: ".encode())
    senha_digitada = conexao.recv(4096).decode()

    if senha_digitada == senha_correta:
        conexao.sendall("Autenticação bem-sucedida. Você está autorizado a realizar downloads.".encode())
        return True
    else:
        conexao.sendall("Senha incorreta. Autenticação falhou.".encode())
        return False
    

# Função para lidar com as solicitações de um cliente
def lidar_com_cliente(conexao, endereco_cliente):
    try:
        if not autenticar_cliente(conexao):
            return  # Se a autenticação falhar, encerra a conexão

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
