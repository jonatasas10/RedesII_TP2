import socket
import threading
import time

def enviar_pacote(dados, endereco_servidor, porta_servidor, sequencia):
    pacote = f"{sequencia}:{dados}"
    servidor_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor_udp_socket.sendto(pacote.encode(), (endereco_servidor, porta_servidor))
    servidor_udp_socket.close()

# Função para enviar uma janela de pacotes
def enviar_janela(janela, endereco_servidor, porta_servidor):
    for i, dados in enumerate(janela):
        enviar_pacote(dados, endereco_servidor, porta_servidor, i)

# Função para listar os arquivos disponíveis no servidor
def listar_arquivos_disponiveis(cliente_socket):
    arquivos_disponiveis = cliente_socket.recv(4096).decode()
    print("Arquivos disponíveis para download:")
    print(arquivos_disponiveis)

# Função para lidar com mensagens do servidor
def lidar_com_mensagens(cliente_socket):
    try:
        while True:
            mensagem = cliente_socket.recv(4096).decode()
            print(mensagem)
    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada.")

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
                time.sleep(0.1)

                # Envia confirmação do pacote recebido
                enviar_pacote("ACK", HOST, PORTA_UDP, int(sequencia))

        # Concatena os dados recebidos para formar o arquivo completo
        arquivo_completo = "".join(pacotes_recebidos)

        with open(nome_arquivo, 'wb') as arquivo:
            arquivo.write(arquivo_completo.encode())

        print(f"Download concluído: {nome_arquivo}")

    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada durante o download.")

# Configurações do cliente
HOST = '127.0.0.1'
PORTA_TCP = 12345
PORTA_UDP = 54321

# Criação do socket TCP do cliente
cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente_socket.connect((HOST, PORTA_TCP))

# Inicia a thread para lidar com mensagens do servidor
thread_mensagens = threading.Thread(target=lidar_com_mensagens, args=(cliente_socket,))
thread_mensagens.start()

try:
    # Autenticação do cliente
    print(cliente_socket.recv(4096).decode())
    senha = input("Digite a senha: ")
    cliente_socket.sendall(senha.encode())

    resposta_autenticacao = cliente_socket.recv(4096).decode()
    print(resposta_autenticacao)

    if "falhou" in resposta_autenticacao.lower():
        raise Exception("Autenticação falhou. Encerrando cliente.")

    while True:
        # Recebe a lista de arquivos do servidor
        listar_arquivos_disponiveis(cliente_socket)

        # Solicitação do cliente para download usando janela deslizante
        nome_arquivo = input("Digite o nome do arquivo que deseja baixar (ou 'sair' para encerrar): ")

        if nome_arquivo.lower() == 'sair':
            cliente_socket.sendall(nome_arquivo.encode())
            break

        download_arquivo(nome_arquivo, cliente_socket)

except KeyboardInterrupt:
    pass

# Fecha a conexão TCP
cliente_socket.close()


# import socket
# import threading

# # Configurações do cliente
# HOST = '127.0.0.1'
# PORTA_TCP = 12345
# PORTA_UDP = 54321


# def receber_arquivo(nome_arquivo):
#     # msg = cliente_socket.recv(4096).decode()
#     # print(msg)

#     udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     udp_socket.bind(('0.0.0.0', PORTA_UDP))
#     dados, endereco_servidor = udp_socket.recvfrom(5242880)

#     with open(nome_arquivo, 'wb') as arquivo:
#         arquivo.write(dados)
#         print(f"Arquivo {nome_arquivo} salvo com sucesso.")
#         arquivo.close ()
#         udp_socket.close()


# # Função para lidar com as mensagens do servidor
# def lidar_com_mensagens(cliente_socket):
#     try:
#         while True:
#             mensagem = cliente_socket.recv(5242880).decode()
#             print(mensagem)
#     except ConnectionResetError:
#         print("Conexão com o servidor foi encerrada.")

# # Criação do socket TCP do cliente
# cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# cliente_socket.connect((HOST, PORTA_TCP))


# # Recebe a lista de arquivos do servidor
# # arquivos_disponiveis = cliente_socket.recv(4096).decode()


# # Inicia a thread para lidar com mensagens do servidor
# # thread_mensagens = threading.Thread(target=lidar_com_mensagens, args=(cliente_socket,))
# # thread_mensagens.start()

# try:
#     # Autenticação do cliente
#     print(cliente_socket.recv(4096).decode())
#     senha = input("Digite a senha: ")
#     cliente_socket.sendall(senha.encode())

#     resposta_autenticacao = cliente_socket.recv(4096).decode()
#     print(resposta_autenticacao)
#     arquivos_disponiveis = cliente_socket.recv(4096).decode()
#     if "falhou" in resposta_autenticacao.lower():
#         raise Exception("Autenticação falhou. Encerrando cliente.")

#     while True:

#             # Recebe a lista de arquivos do servidor # aqui estava dando erro logo aops recebimento, passou para cima.
#             # arquivos_disponiveis = cliente_socket.recv(4096).decode()  # o recv() nao precisa ser deste tamanho, pode ser menor '4096'.
        
#             print("Arquivos disponíveis para download:")
#             print(arquivos_disponiveis)
        
#             # Solicitação do cliente para download usando UDP
#             nome_arquivo = input("Digite o nome do arquivo que deseja baixar (ou 'sair' para encerrar): ")

#             if nome_arquivo.lower() == 'sair':
#                 cliente_socket.sendall(nome_arquivo.encode())
#                 print('Desconectando do servidor...\n')
#                 print('Saindo...\n')
#                 break

#             cliente_socket.sendall(nome_arquivo.encode())
#             receber_arquivo(nome_arquivo)
            
#             # continuar = input('deseja continuar? Digite S ou N.')
#             # if continuar.lower() == 'n':
#             #     print('Saindo...\n')
#             #     break
                
# except KeyboardInterrupt:
#     pass


# # # Fecha a conexão TCP
# cliente_socket.close()

