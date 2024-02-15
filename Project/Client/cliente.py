import socket, select
import os
from dotenv import load_dotenv
import pickle, time
from numpy import random
import zlib
load_dotenv()

# Configurações do cliente
dir = os.path.dirname(__file__)
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))
client_files_path = os.path.join(dir, os.environ.get("CLIENT_FILES_PATH"))

def random_delay():
    random_delay = random.uniform(0.15, 1)
    time.sleep(random_delay)

def calcular_checksum(data):
    return zlib.crc32(data)

def velocidade_download(endereco_servidor, tam_pacote, atraso):
        print(f"Conexão de {endereco_servidor}")                
        download_speed = tam_pacote*8 / atraso
        download_speed /= 10^6
        print(f"\nDelay de conexão: {round(atraso,2)} segundos")
        print(f"Velocidade de download: {round(download_speed, 2)} Mbps\n")

def receber_arquivo(udp_socket, nome_arquivo):
    
    numero_sequencia_esperado = 0
    buffer = 1500
    with open(os.path.join(client_files_path, nome_arquivo), 'wb') as arquivo:
        while True:
            try:
                tempo_inicial = time.time()
                random_delay() # TODO: DELAY AQUI
                packet, address = udp_socket.recvfrom(buffer)
                
                sequence_number_bytes = packet[:4]  # Extrai apenas os 4 primeiros bytes
                checksum_recebido = int.from_bytes(packet[4:8], byteorder='big')
                checkum = calcular_checksum(packet[8:])                                
                sequence_number = int.from_bytes(sequence_number_bytes, byteorder='big')

                if  'eof'.encode('utf8') in packet[4:]:                    
                    break

                if sequence_number == numero_sequencia_esperado and checksum_recebido == checkum:
                    print(f"recebido {sequence_number} {numero_sequencia_esperado}")
                    arquivo.write(packet[8:])
                    ack = str(sequence_number)
                    tempo_final = time.time()
                    tam_pacote = len(packet)
                    atraso = tempo_final - tempo_inicial
                   # print(atraso)
                    velocidade_download(address, tam_pacote, atraso)

                    random_delay() # TODO: DELAY AQUI
                    udp_socket.sendto(str(numero_sequencia_esperado).encode(), address)
                    
                    numero_sequencia_esperado += 1 
                else:
                    print(f"Falha {sequence_number} != {numero_sequencia_esperado}")
                    udp_socket.sendto(str(numero_sequencia_esperado).encode(), address)

            except socket.timeout:
                print("Timeout. Conexão encerrada.")
                break

    print(f"Arquivo {nome_arquivo} recebido com sucesso.")
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

def client():
    try:
        while True:
            # Criação do socket UDP do cliente
            cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cliente_socket.sendto("start".encode(), (HOST, PORTA_UDP))
            # Recebe a lista de arquivos do servidor # aqui estava dando erro logo aops recebimento, passou para cima.
            arquivos_disponiveis = cliente_socket.recv(1500).decode()

            print(arquivos_disponiveis)

            nome_arquivo = input("Nome do arquivo, sair ou upload: ")
            if nome_arquivo == "sair":
                break

            if nome_arquivo == "upload":
                # auth then upload
                arquivos_para_upload = os.listdir(client_files_path)
                pass

            while nome_arquivo not in arquivos_disponiveis:
                print("Arquivo indisponível. Tente novamente.")
                nome_arquivo = input("Nome do arquivo: ")

            cliente_socket.sendto(nome_arquivo.encode(), (HOST, PORTA_UDP))
            receber_arquivo(cliente_socket, nome_arquivo)
            print("Recebimento concluido.")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cliente_socket.close()

if __name__ == "__main__":
    main()