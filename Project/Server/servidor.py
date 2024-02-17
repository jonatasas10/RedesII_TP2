import socket, select, traceback, queue
import os
import threading
from dotenv import load_dotenv
from numpy import random
import zlib
import numpy as np
import hashlib

from time import time, sleep
load_dotenv()

dir = os.path.dirname(__file__)
server_files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))

def calcular_md5(arquivo):   
    md5_hash = None
    with open(arquivo,'rb') as arquivo:
        arquivo_md5 = arquivo.read()            
        md5_hash = hashlib.md5(arquivo_md5).hexdigest()
    return md5_hash  

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
            ACK = int(dados.decode('utf8')) if dados.isdigit() else dados.decode('utf8')
            print("ACK recebido", ACK)
            resultado.put(ACK)
        
    resultado.put("ACK não recebido")

def enviar_pacote(servidor_socket, endereco_cliente,packet, est_rtt):
    if est_rtt is None:
        sleep(0.005)
    else:
        sleep(est_rtt)    
    servidor_socket.sendto(packet, endereco_cliente)



# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(server_files_path)

# Função para enviar um arquivo para o cliente usando UDP
def enviar_arquivo(nome_arquivo, endereco_cliente, servidor_socket):
    try:
        with open(os.path.join(server_files_path, nome_arquivo), 'rb') as arquivo: 
            md5_file = calcular_md5(os.path.join(server_files_path, nome_arquivo)) 
            buffer = 1450         
            numero_sequencia_base = 0
            proximo_numero_sequencia = 0
            arquivo.seek(numero_sequencia_base)
            N = 100
            
            tentativa_reenvio = 0
            est_rtt = None
            dev_rtt = None
            timeout = None
            quantidade_pct_enviado = 0
            quantidade_pct_perdido = 0
            eof = False
            tempo_dict = {}
            chegada_dict = {}
            total_perdidos = 0
            
            ultimo_ack = None
            while True:                
                
                i = proximo_numero_sequencia                
                if (proximo_numero_sequencia < numero_sequencia_base + N) and eof is False:                
                    
                    arquivo.seek(i * buffer)  # Move o ponteiro do arquivo para o byte correspondente
                    packet = bytearray()
                    packet.extend(i.to_bytes(4, byteorder='big')) 
                    dados = arquivo.read(buffer) # Adiciona o numero de sequência ao pacote
                    checksum = calcular_checksum(dados)                    
                    packet.extend(checksum.to_bytes(4, byteorder='big'))
                    if len(dados) < 1450:   
                        packet.extend(b"#fim")                                               
                        eof = True
                    packet.extend(dados)  
                    chegada_dict[i] = time()
                                                                
                    threading.Thread(target=enviar_pacote, args=[servidor_socket, endereco_cliente, packet, est_rtt]).start()                                             
                    quantidade_pct_enviado += 1                        
                    proximo_numero_sequencia = proximo_numero_sequencia + 1 #if len(dados) == 1450 else proximo_numero_sequencia
                    
                resultado = queue.Queue()                    
                threading.Thread(target=receber_ack, args=[servidor_socket, resultado]).start()
                resultado_ack = resultado.get()

                if  resultado_ack not in ["ACK não recebido", "#eof", "nack"] and numero_sequencia_base == int(resultado_ack):
                    tentativa_reenvio = 0
                    N  = N + 1 if N < 128 else N
                    tempo_dict[numero_sequencia_base] = time()
                    
                    tempo_dict[numero_sequencia_base] = tempo_dict[numero_sequencia_base] - chegada_dict[numero_sequencia_base]                                          
                    
                    atraso = tempo_dict[numero_sequencia_base]                                       
                    est_rtt, dev_rtt = calcular_rtt(est_rtt, dev_rtt, atraso)
                    timeout = 4*dev_rtt + est_rtt
                    
                    print(f"RTT estimado: {round(est_rtt,2)}, DevRTT: {round(dev_rtt,2)}, timeout: {round(timeout,2)}")
                    del tempo_dict[numero_sequencia_base]
                    del chegada_dict[numero_sequencia_base]
                    numero_sequencia_base = int(resultado_ack) + 1
                 
                else:
                    tempo_dict[numero_sequencia_base] = time()                                        
                    tempo_dict[numero_sequencia_base] = tempo_dict[numero_sequencia_base] - chegada_dict[numero_sequencia_base]                     
                    atraso = tempo_dict[numero_sequencia_base]                                       
                                       
                    timeout = 2 if timeout is None else timeout  
                    if (resultado_ack not in ["ACK não recebido", "#eof", "nack"] and
                        int(resultado_ack) == numero_sequencia_base-1 and ultimo_ack == int(resultado_ack)):
                        ultimo_ack = int(resultado_ack)
                        tentativa_reenvio += 1
                        quantidade_pct_perdido += 1
                        total_perdidos += (proximo_numero_sequencia - numero_sequencia_base)
                        proximo_numero_sequencia =  ultimo_ack + 1
                        numero_sequencia_base = proximo_numero_sequencia
                        
                        #est_rtt += 0.001
                        eof = False
                    
                    elif tempo_dict[numero_sequencia_base] > timeout: #TODO verificar esse tempo 0.6s
                        tentativa_reenvio += 1
                        quantidade_pct_perdido += 1
                        total_perdidos += (proximo_numero_sequencia - numero_sequencia_base)
                        #timeout = timeout + 0.005                                             
                        #est_rtt += 0.005
                        N = 100
                        proximo_numero_sequencia =  numero_sequencia_base          
                        eof = False
                
                if eof and resultado_ack == "#eof":                                                      
                    break              
            
            servidor_socket.setblocking(True)
            print("Quantidade de pacotes enviados:", quantidade_pct_enviado)
            print("Quantidade de pacotes perdidos:", total_perdidos)
            print(f"Proporção: {round((total_perdidos/quantidade_pct_enviado)*100,2)}%")
            
            print("MD% HASH", md5_file)
            servidor_socket.sendto(md5_file.encode(), endereco_cliente)

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
