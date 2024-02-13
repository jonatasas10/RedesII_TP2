import socket, select
import os
from dotenv import load_dotenv
import pickle

load_dotenv()

# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))


def receber_arquivo(udp_socket, nome_arquivo):
    #udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #udp_socket.bind(('0.0.0.0', PORTA_UDP))
    pacote_final = []
    proximo_numero_sequencia = 0

    while True:

        dados, endereco_servidor = udp_socket.recvfrom(102)
        #print(endereco_servidor)
        print(dados.decode('utf8'))
        if dados.decode() == 'eof':
            #udp_socket.sendto('eof'.encode(), endereco_servidor)
            break

        numero_seq, endereco_servidor = udp_socket.recvfrom(10)
        print("\nTAMANHO DO PACOTE", len(dados), " / NUMERO SEQUENCIA", numero_seq.decode())
        print("\n")
        numero_seq = int(numero_seq.decode())
        if proximo_numero_sequencia == 5:
             udp_socket.sendto('5'.encode(), endereco_servidor)
             udp_socket.sendto('5'.encode(), endereco_servidor)

        if len(dados) > 50:
            print("Prox:", numero_seq, proximo_numero_sequencia)
            if numero_seq == proximo_numero_sequencia:
                udp_socket.sendto(str(proximo_numero_sequencia).encode('utf8'), endereco_servidor)
                proximo_numero_sequencia = proximo_numero_sequencia + 1

            else:

                udp_socket.sendto(str(proximo_numero_sequencia - 1).encode('utf8'), endereco_servidor)


    with open(nome_arquivo, 'wb') as arquivo:
        arquivo.write(dados)
        print(f"Arquivo {nome_arquivo} salvo com sucesso.")
        arquivo.close ()
        #udp_socket.close()


# Função para lidar com as mensagens do servidor
def lidar_com_mensagens(cliente_socket):
    try:
        while True:
            mensagem = cliente_socket.recv(5242880).decode()
            print(mensagem)
    except ConnectionResetError:
        print("Conexão com o servidor foi encerrada.")




# Inicia a thread para lidar com mensagens do servidor
# thread_mensagens = threading.Thread(target=lidar_com_mensagens, args=(cliente_socket,))
# thread_mensagens.start()

def main():
    try:
        # Criação do socket UDP do cliente
        cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cliente_socket.sendto("start".encode(), (HOST, PORTA_UDP))
        # Recebe a lista de arquivos do servidor # aqui estava dando erro logo aops recebimento, passou para cima.
        arquivos_disponiveis = cliente_socket.recv(4096).decode()

        nome_arquivo = "Tp02.txt"

        cliente_socket.sendto(nome_arquivo.encode(), (HOST, PORTA_UDP))
        receber_arquivo(cliente_socket, nome_arquivo)
        print("recebido")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cliente_socket.close()

if __name__ == "__main__":
    main()
"""
try:

    # Criação do socket TCP do cliente
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #cliente_socket.connect((HOST, PORTA_TCP))


    while True:
        cliente_socket.sendto("start".encode(), (HOST, PORTA_UDP))
        # Recebe a lista de arquivos do servidor
        arquivos_disponiveis = cliente_socket.recv(4096).decode()
        # Recebe a lista de arquivos do servidor # aqui estava dando erro logo aops recebimento, passou para cima.
        # arquivos_disponiveis = cliente_socket.recv(4096).decode()  # o recv() nao precisa ser deste tamanho, pode ser menor '4096'.

        print("Arquivos disponíveis para download:")
        print(arquivos_disponiveis)

        # Solicitação do cliente para download usando UDP
        nome_arquivo = "Tp02.txt"#input("Digite o nome do arquivo que deseja baixar (ou 'sair' para encerrar): ")

        if nome_arquivo.lower() == 'sair':
            cliente_socket.sendto(nome_arquivo.encode(), (HOST, PORTA_UDP))
            # cliente_socket.close()
            break

        cliente_socket.sendto(nome_arquivo.encode(), (HOST, PORTA_UDP))

        #cliente_socket.sendto(nome_arquivo.encode(), (HOST, PORTA_UDP))
        receber_arquivo(cliente_socket, nome_arquivo)
        print("recebido")
        cliente_socket.sendto("fim".encode(), (HOST, PORTA_UDP))

except KeyboardInterrupt:
    pass

"""
# # Fecha a conexão TCP
#cliente_socket.close()
