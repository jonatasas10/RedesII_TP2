import socket, select
import os
from dotenv import load_dotenv
import pickle, time
from numpy import random
import zlib
load_dotenv()

# Configurações do cliente
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))

def random_delay():
    random_delay = random.uniform(0.15, 1)
    time.sleep(random_delay)

def calcular_checksum(data):
    return zlib.crc32(data)

def velocidade_download(endereco_servidor, tam_pacote, atraso):
        print(f"Connection from {endereco_servidor}")                
        download_speed = tam_pacote*8 / atraso
        download_speed /= 10^6
        print(f"\nConnection delay: {round(atraso,2)} seconds")
        print(f"Download speed: {round(download_speed, 2)} Mbps\n")

def receber_arquivo(udp_socket, nome_arquivo):
    
    expected_sequence_number = 0
    buffer = 1500
    with open(nome_arquivo, 'wb') as arquivo:
        while True:
            try:
                tempo_inicial = time.time()
                random_delay()
                packet, address = udp_socket.recvfrom(buffer)
                
                sequence_number_bytes = packet[:4]  # Extrai apenas os 4 primeiros bytes
                checksum_recebido = int.from_bytes(packet[4:8], byteorder='big')
                checkum = calcular_checksum(packet[8:])                                
                sequence_number = int.from_bytes(sequence_number_bytes, byteorder='big')

                if  'eof'.encode('utf8') in packet[4:]:                    
                    break

                if sequence_number == expected_sequence_number and checksum_recebido == checkum:
                    print(f"recebido {sequence_number} {expected_sequence_number}")
                    arquivo.write(packet[8:])
                    ack = str(sequence_number)
                    tempo_final = time.time()
                    tam_pacote = len(packet)
                    atraso = tempo_final - tempo_inicial
                   # print(atraso)
                    velocidade_download(address, tam_pacote, atraso)

                    random_delay()
                    udp_socket.sendto(str(expected_sequence_number).encode(), address)
                    
                    expected_sequence_number += 1 
                else:
                    print(f"Falha {sequence_number} != {expected_sequence_number}")
                    udp_socket.sendto(str(expected_sequence_number).encode(), address)

            except socket.timeout:
                print("Timeout. Conexão encerrada.")
                break

    print(f"Arquivo {nome_arquivo} recebido com sucesso.")
    #ack = str(-1)
    #udp_socket.sendto(ack.encode(), address)

    #udp_socket.close()

# Função para lidar com as mensagens do servidor
def lidar_com_mensagens(cliente_socket):
    try:
        while True:
            mensagem = cliente_socket.recv(1500).decode()
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
        arquivos_disponiveis = cliente_socket.recv(1500).decode()

        nome_arquivo = "Tp02.txt"#"TP02D.pdf"

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
