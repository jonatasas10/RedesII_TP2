import socket, select, traceback, queue
import os
import threading
from dotenv import load_dotenv
from numpy import random
import zlib
import numpy as np

from time import time, sleep
load_dotenv()

dir = os.path.dirname(__file__)
server_files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))

def random_delay(media):
    
    media = 0.001 if media < 0.00001 else media
    print(media)
    random_delay = random.uniform(0.01, media)
    sleep(random_delay)

def calcular_rtt(est_rtt, dev_rtt, amostra):
    alpha = 0.125
    beta = 0.125
    if est_rtt is None:
        est_rtt = amostra
    else:
        est_rtt = (1 - alpha)*est_rtt + alpha*amostra
    if dev_rtt is None:
        dev_rtt = abs(amostra - est_rtt)
    else:
        dev_rtt = (1 - beta)*dev_rtt + beta*abs(amostra - est_rtt)
    return est_rtt, dev_rtt

def calcular_checksum(data):
    return zlib.crc32(data)

def get_network_status(servidor_socket, endereco_cliente, tam_pacote, atraso):
        #print(f"Connection from {endereco_cliente}")
    
        atraso = 0.000001 if atraso == 0 else atraso #para não dar erro de divisão por 0
        download_speed = tam_pacote*8 / atraso
        download_speed /= 10**6
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

def enviar_pacote(servidor_socket, endereco_cliente,packet, est_rtt):
    if est_rtt is None:
        sleep(0.001)
    else:
        sleep(est_rtt*0.9)    
    servidor_socket.sendto(packet, endereco_cliente)



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
            N = 50
            tempo_chegada = [0 for x in range(N)]
            tempo = [0 for x in range(N)]
            window_size_inicial = N  # Define o tamanho da janela
            window_start = 0  # Começa a janela em 0
            tentativa_reenvio = 0
            est_rtt = None
            dev_rtt = None
            timeout = 0
            quantidade_pct_enviado = 0
            quantidade_pct_perdido = 0
            eof = False

            while True:
                bytes_restantes = os.path.getsize(os.path.join(server_files_path, nome_arquivo)) - window_start
                #print(f"Remaining bytes: {bytes_restantes}")
                window_size = min(window_size_inicial, bytes_restantes)
                
                if window_size <= 0:
                    eof = True
                else:
                    eof = False # se tiver retransmissão tem que voltar

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
                        threading.Thread(target=enviar_pacote, args=[servidor_socket, endereco_cliente, packet, est_rtt]).start()
                        #servidor_socket.sendto(packet, endereco_cliente)                        

                        quantidade_pct_enviado += 1
                        print(f"Número de sequência atual: {proximo_numero_sequencia}.")
                        #input("")
                        proximo_numero_sequencia += 1
                
                resultado = queue.Queue()                    
                threading.Thread(target=receber_ack, args=[servidor_socket, resultado]).start()
                resultado_ack = resultado.get()
                
                if  resultado_ack != "ACK não recebido" and not eof:
                    tentativa_reenvio = 0
                    
                    numero_sequencia_base = int(resultado_ack) + 1
                    window_start = numero_sequencia_base*buffer                    
                    tempo = timeout_ack(numero_sequencia_base - 1, tempo_chegada, tempo, N)
                    
                    atraso = tempo[numero_sequencia_base - 1] if numero_sequencia_base < N else tempo[N-1]                                        
                    est_rtt, dev_rtt = calcular_rtt(est_rtt, dev_rtt, atraso)
                    timeout = 4*dev_rtt + est_rtt
                    print(f"RTT estimado: {round(est_rtt,2)}, DevRTT: {round(dev_rtt,2)}, timeout: {round(timeout,2)}")
                    #get_network_status(servidor_socket, endereco_cliente, len(packet), atraso)

                elif i == numero_sequencia_base + N:                        
                    tempo = timeout_ack(numero_sequencia_base, tempo_chegada, tempo, N)
                    indice = numero_sequencia_base if numero_sequencia_base < N else N - 1
                    timeout = 5 if timeout is None else timeout
                    if tempo[indice] > timeout: #TODO verificar esse tempo 0.6s
                        print("ACK", numero_sequencia_base, "não recebido a tempo.")                      
                        tentativa_reenvio += 1
                        quantidade_pct_perdido += 1
                        print(f"tentativa de reenvio: {tentativa_reenvio}")
                        proximo_numero_sequencia =  numero_sequencia_base - 1
                        #input("")
                elif eof and resultado_ack != "ACK não recebido" and numero_sequencia_base != int(resultado_ack):
                    eof = False                    
                    proximo_numero_sequencia =  numero_sequencia_base - 1 if numero_sequencia_base > 0 else 0
                        
                elif eof and numero_sequencia_base == proximo_numero_sequencia:    
                                   
                    break
            
            packet.extend((0).to_bytes(4, byteorder='big'))  
            packet.extend('eof'.encode())
            servidor_socket.sendto(packet, endereco_cliente)
            """
            if tentativa_reenvio < 10:
                print(f"Arquivo {nome_arquivo} enviado para {endereco_cliente}")
            else:
                print(f"Arquivo {nome_arquivo} não enviado para {endereco_cliente}, timeout de envio")
            """   
            servidor_socket.setblocking(True)
            print("QTD PCT ENVIADO:", quantidade_pct_enviado)
            print("PERDIDO:", quantidade_pct_perdido)

    except FileNotFoundError:
        print(f"Arquivo {nome_arquivo} não encontrado no servidor.")
    except Exception as e:
        print("Algum outro erro:", e)
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
        if nome_arquivo == "sair" or nome_arquivo == "start":
            return
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
            
            if not descartar and "start" in mensagem.decode():
                print(descartar, mensagem)
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
