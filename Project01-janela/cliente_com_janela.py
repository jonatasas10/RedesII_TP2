import socket
import os
from dotenv import load_dotenv

import time

load_dotenv()


# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))


def enviar_pacote(dados, endereco_servidor, porta_servidor, sequencia):
    pacote = f"{sequencia}:{dados}"
    servidor_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor_udp_socket.sendto(pacote.encode(), (endereco_servidor, porta_servidor))
    servidor_udp_socket.close()

# Função para enviar uma janela de pacotes
def enviar_janela(janela, endereco_servidor, porta_servidor):
    for i, dados in enumerate(janela):
        enviar_pacote(dados, endereco_servidor, porta_servidor, i)


# # Função para listar os arquivos disponíveis no servidor
# def listar_arquivos_disponiveis(cliente_socket):
#     arquivos_disponiveis = cliente_socket.recv(4096).decode()
#     print("Arquivos disponíveis para download:")
#     print(arquivos_disponiveis)


# Função para lidar com as mensagens do servidor
def lidar_com_mensagens(cliente_socket): # OK
    try:
        while True:
            mensagem = cliente_socket.recv(5242880).decode()
            print(mensagem)
    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada.")


# def receber_arquivo(nome_arquivo):
#     udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     udp_socket.bind(('0.0.0.0', PORTA_UDP))
#     dados, endereco_servidor = udp_socket.recvfrom(5242880)

#     with open(nome_arquivo, 'wb') as arquivo:
#         arquivo.write(dados)
#         print(f"Arquivo {nome_arquivo} salvo com sucesso.")
#         arquivo.close ()
#         udp_socket.close()

# Função para download usando janela deslizante
def download_arquivo(nome_arquivo, cliente_socket):
    try:
        cliente_socket.sendall(nome_arquivo.encode())
        resposta = cliente_socket.recv(4096).decode()

        if "não autorizado" in resposta.lower():
            print("Você não está autorizado a realizar downloads.")
            return

        print(f"Iniciando download do arquivo {nome_arquivo}")

        pacotes_recebidos = []
        sequencia_esperada = 0

        while True:
            dados, _ = cliente_socket.recvfrom(4096)
            sequencia, dados = dados.decode().split(':')

            if int(sequencia) == sequencia_esperada:
                if dados == "EOF":
                    break  # Fim do arquivo
                pacotes_recebidos.append(dados)
                sequencia_esperada += 1

                # Simula o tempo de transmissão
                time.sleep(1.1)

                # Envia confirmação do pacote recebido
                enviar_pacote("ACK", HOST, PORTA_UDP, int(sequencia))

        # Concatena os dados recebidos para formar o arquivo completo
        arquivo_completo = "".join(pacotes_recebidos)

        with open(nome_arquivo, 'wb') as arquivo:
            arquivo.write(arquivo_completo.encode())

        print(f"Download concluído: {nome_arquivo}")
        arquivo.close ()
        # udp_socket.close()
    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada durante o download.")


# Criação do socket TCP do cliente
cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente_socket.connect((HOST, PORTA_TCP))

# Inicia a thread para lidar com mensagens do servidor
# thread_mensagens = threading.Thread(target=lidar_com_mensagens, args=(cliente_socket,))
# thread_mensagens.start()

# Autenticação do cliente
  
try:
    print(cliente_socket.recv(4096).decode())
    senha = input("Digite a senha para conectarse ao serviço de donwload: ")
    cliente_socket.sendall(senha.encode())

    resposta_autenticacao = cliente_socket.recv(4096).decode()
    print(resposta_autenticacao)
    arquivos_disponiveis = cliente_socket.recv(4096).decode()
    
    if "falhou" in resposta_autenticacao.lower():
        raise Exception("Autenticação falhou. Encerrando cliente.")
  
    while True:
            
            print("Arquivos disponíveis para download:")
            print(arquivos_disponiveis)
        
            # Solicitação do cliente para download usando UDP
            nome_arquivo = input("Digite o nome do arquivo que deseja baixar (ou 'sair' para encerrar): ")

            if nome_arquivo.lower() == 'sair':
                cliente_socket.sendall(nome_arquivo.encode())
                # cliente_socket.close()
                print('\nSaindo...\n')
                break

            # cliente_socket.sendall(nome_arquivo.encode())
            # receber_arquivo(nome_arquivo)
            download_arquivo(nome_arquivo, cliente_socket)
            
           
except KeyboardInterrupt:
    pass


# # Fecha a conexão TCP
cliente_socket.close()

