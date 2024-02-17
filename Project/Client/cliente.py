import socket, select
import os
from dotenv import load_dotenv
import pickle, time
from numpy import random
import zlib
load_dotenv()
import hashlib
# Configurações do cliente
dir = os.path.dirname(__file__)
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))
client_files_path = os.path.join(dir, os.environ.get("CLIENT_FILES_PATH"))

def calcular_md5(arquivo):   
    md5_hash = None
    with open(arquivo,'rb') as arquivo:
        arquivo_md5 = arquivo.read()            
        md5_hash = hashlib.md5(arquivo_md5).hexdigest()
    return md5_hash   
        
def calcular_checksum(data):
    return zlib.crc32(data)

def velocidade_download(tam_pacote, atraso):
        #print(f"Conexão de {endereco_servidor}")                
        download_speed = tam_pacote*8 / (atraso*10**6)
        print(f"\nDelay de conexão: {round(atraso,2)} segundos")
        print(f"Velocidade de download: {round(download_speed, 2)} Mbps\n")

def receber_arquivo(udp_socket, nome_arquivo):
    
    numero_sequencia_esperado = 0
    buffer = 1500
    tam_arquivo = 0
    tam_final_pacote = 0
    count = 0
    eof = False
    with open(os.path.join(client_files_path, nome_arquivo), 'wb') as arquivo:
        tempo = time.time()
        while True:
            try:
                tempo_inicial = time.time()
                                
                packet, address = udp_socket.recvfrom(buffer)   
                count+= 1                             
                sequence_number_bytes = packet[:4]  # Extrai apenas os 4 primeiros bytes
                checksum_recebido = int.from_bytes(packet[4:8], byteorder='big')
                sequence_number = int.from_bytes(sequence_number_bytes, byteorder='big')
                if "#fim".encode() in packet[8:12]:# and len(packet) < 80:   
                    eof = True  if sequence_number == numero_sequencia_esperado else eof
                    checkum = calcular_checksum(packet[12:])  
                else:
                    checkum = calcular_checksum(packet[8:])                                                                                               

                if sequence_number == numero_sequencia_esperado and checksum_recebido == checkum:
                    print(f"recebido {sequence_number} {numero_sequencia_esperado}")
                    arquivo.write(packet[8:]) if eof == False else arquivo.write(packet[12:])               
                    tempo_final = time.time()
                    tam_pacote = len(packet[8:]) if eof == False else len(packet[12:])
                    tam_arquivo += tam_pacote
                    tam_final_pacote += len(packet) #para cálculo da vazão
                    atraso = tempo_final - tempo_inicial
                    #velocidade_download(address, tam_pacote, atraso)

                    #random_delay() # TODO: DELAY AQUI
                    if eof == False:
                        udp_socket.sendto(str(numero_sequencia_esperado).encode(), address)
                    else:                       
                        udp_socket.sendto("#eof".encode(), address)
                        break
                   
                    numero_sequencia_esperado += 1 
                    
                    
                else:                    
                    print(f"Falha {sequence_number} != {numero_sequencia_esperado}")
                    udp_socket.sendto(f"{numero_sequencia_esperado-1}".encode(), address)

               
            except socket.timeout:
                print("Timeout. Conexão encerrada.")
                break
        tempo_envio = time.time() - tempo
        print(f"Tempo final para enviar o arquivo: {round(tempo_envio, 2)} segundos")
    
    vazao = (tam_final_pacote*8) / (tempo_envio*10**6)
    print(f"Tamanho do arquivo: {tam_arquivo} bytes.")
    print(f"Vazão: {round(vazao,3)} Mbps.")    
    print(f"Arquivo {nome_arquivo} recebido com sucesso. \n")

    md5_file = calcular_md5(os.path.join(client_files_path, nome_arquivo))
    print(f"MD5 HASH Calculado: {md5_file}")
    
    while True:
        packet, address = udp_socket.recvfrom(buffer) 
        if "#checksum".encode() in packet[0:10]: #descartando pacotes retransmitidos anteriores        
            break
        
    checksum_recebido = int.from_bytes(packet[9:13], byteorder='big')  
    md5_hash_recebido = None
    checksum = calcular_checksum(md5_file.encode())

    if checksum == checksum_recebido:                
        md5_hash_recebido = packet[13:].decode()
    else:
        print(f"Checksum não é válido. Recebido: {checksum_recebido}, calculado: {checksum}")
        
    
    print("MD5 recebido:", md5_hash_recebido)
    if md5_file == md5_hash_recebido:
        print("Os hashes dos arquivos são iguais.\n")
    else:
        print("Os hashes dos arquivos são diferentes.\n")
    
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
    except KeyboardInterrupt:
        cliente_socket.sendto("sair".encode(), (HOST, PORTA_UDP))
    finally:
        cliente_socket.close()

if __name__ == "__main__":
    client()