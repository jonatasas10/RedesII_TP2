import socket, select, traceback, queue
import os
import threading
from dotenv import load_dotenv
from numpy import random
import zlib

from time import time, sleep
load_dotenv()

dir = os.path.dirname(__file__)
server_files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))

def random_delay():
    random_delay = random.uniform(0, 0.2)
    sleep(random_delay)

def calcular_checksum(data):
    return zlib.crc32(data)

def get_network_status(servidor_socket, endereco_cliente, tam_pacote, atraso):
        print(f"Connection from {endereco_cliente}")
    
        atraso = 0.1 if atraso == 0 else atraso
        download_speed = tam_pacote*8 / atraso
        download_speed /= 10^6
        print(f"Connection delay: {atraso} seconds")
        print(f"Download speed: {round(download_speed, 2)} Mbps")

def receber_ack(servidor_socket, resultado):
    servidor_socket.setblocking(False)
    ler_socket, _, _ = select.select([servidor_socket], [], [], 0.0)
    #random_delay()
    for s in ler_socket:
        if s is servidor_socket:
            dados, _ = servidor_socket.recvfrom(100)
            ACK = int(dados.decode('utf8'))
            print("ACK recebido", ACK)
            resultado.put(ACK)
        
    resultado.put("ACK não recebido")

# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(server_files_path)

def timeout_ack(numero_sequencia_base, tempo_chegada, tempo, N):
    
    if numero_sequencia_base < N:       
        tempo_ack = (time() - tempo_chegada[numero_sequencia_base])        
        tempo_ack = round(tempo_ack,3)                
        tempo[numero_sequencia_base] = tempo_ack 
    else: 
        tempo_ack = (time() - tempo_chegada[N-1])
        tempo_ack = round(tempo_ack,3)  
        tempo = tempo[1:] + [tempo_ack]
    
    return tempo

# Função para enviar um arquivo para o cliente usando UDP
def enviar_arquivo(nome_arquivo, endereco_cliente, servidor_socket):
    try:
        with open(os.path.join(server_files_path, nome_arquivo), 'rb') as arquivo:  
            buffer = 1450         
            numero_sequencia_base = 0
            proximo_numero_sequencia = 0
            arquivo.seek(numero_sequencia_base)
            N = 4
            tempo_chegada = [0 for x in range(N)]
            tempo = [0 for x in range(N)]
            window_size_inicial = 4  # Define o tamanho da janela
            window_start = 0  # Começa a janela em 0
            threshold = 8  # Define o limite de reenvio do payload 
            tentativa_reenvio = 0
            eof = False

            while True:
                bytes_restantes = os.path.getsize(os.path.join(server_files_path, nome_arquivo)) - window_start
                #print(f"Remaining bytes: {bytes_restantes}")
                window_size = min(window_size_inicial, bytes_restantes)
                
                if window_size <= 0:
                    eof = True

                if tentativa_reenvio >= 10:
                    eof = True
                    break

                i = proximo_numero_sequencia
                if proximo_numero_sequencia < numero_sequencia_base + N and not eof:                
                    
                    arquivo.seek(i * buffer)  # Move o ponteiro do arquivo para o byte correspondente
                    packet = bytearray()
                    packet.extend(i.to_bytes(4, byteorder='big')) 
                    dados = arquivo.read(buffer) # Adiciona o numero de sequência ao pacote
                    checksum = calcular_checksum(dados)
                    
                    packet.extend(checksum.to_bytes(4, byteorder='big'))
                    packet.extend(dados)  
                    
                    if i < N:                           
                        tempo_chegada[i] = time()
                    else: 
                        tempo_chegada = tempo_chegada[1:] + [time()]
                    #print(f"Enviando payload {i}")
                    if dados:
                        
                        servidor_socket.sendto(packet, endereco_cliente)
                        print("Índice da janela enviada:", i)
                        proximo_numero_sequencia += 1
                
                resultado = queue.Queue()                    
                threading.Thread(target=receber_ack, args=[servidor_socket, resultado]).start()
                resultado_ack = resultado.get()
                
                if  resultado_ack != "ACK não recebido" and not eof:
                    tentativa_reenvio = 0

                    numero_sequencia_base = int(resultado_ack) + 1
                    window_start = numero_sequencia_base*buffer                    
                    tempo = timeout_ack(numero_sequencia_base - 1, tempo_chegada, tempo, N)
                    
                    print("TEMPO DE RESPOSTA:", tempo)
                    atraso = tempo[numero_sequencia_base - 1] if numero_sequencia_base < N else tempo[N-1]
                    get_network_status(servidor_socket, endereco_cliente, len(packet), atraso)

                elif i == numero_sequencia_base + N:                        
                    tempo = timeout_ack(numero_sequencia_base, tempo_chegada, tempo, N)

                    if tempo[numero_sequencia_base] > 0.6:
                        print("ACK", numero_sequencia_base, "não recebido a tempo.")
                        
                        tentativa_reenvio += 1
                        print(f"tentativa de reenvio: {tentativa_reenvio}")

                        proximo_numero_sequencia = numero_sequencia_base

                        print("Tempo atual - retransmissão:", tempo)
                    elif eof and numero_sequencia_base == proximo_numero_sequencia:
                        break
                                       
            packet.extend((0).to_bytes(4, byteorder='big'))  
            packet.extend('eof'.encode())
            servidor_socket.sendto(packet, endereco_cliente)

            if tentativa_reenvio < 10:
                print(f"Arquivo {nome_arquivo} enviado para {endereco_cliente}")
            else:
                print(f"Arquivo {nome_arquivo} não enviado para {endereco_cliente}, timeout de envio")
                
            servidor_socket.setblocking(True)

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
            print(f"Servidor ouvindo em {HOST}:{PORTA_UDP}")
            mensagem, endereco_cliente = servidor_socket.recvfrom(1024)
            descartar = mensagem.isdigit()
            
            if not descartar:
                lidar_com_cliente(servidor_socket, endereco_cliente)
            else:
                print("Pacote descartado.")

    except KeyboardInterrupt:
        print("\nEncerrando socket do servidor.")
        servidor_socket.close()
    finally:
        servidor_socket.close()

if __name__ == "__main__":
    main()
