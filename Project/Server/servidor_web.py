import socket, select, traceback, queue
import os
import threading
from dotenv import load_dotenv
from numpy import random
import zlib

from time import sleep, time
load_dotenv()

dir = os.path.dirname(__file__)
server_files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))


def velocidade_download(endereco_servidor, tam_pacote, atraso):
        print(f"Conexão de {endereco_servidor}")                
        download_speed = tam_pacote*8 / atraso
        download_speed /= 10^6
        print(f"\nDelay de conexão: {round(atraso,2)} segundos")
        print(f"Velocidade de download: {round(download_speed, 2)} Mbps\n")

def receber_arquivo(udp_socket, nome_arquivo):
    
    numero_sequencia_esperado = 0
    buffer = 1500
    with open(os.path.join(server_files_path, nome_arquivo), 'wb') as arquivo:
        while True:
            try:
                tempo_inicial = time()
                random_delay() # TODO: DELAY AQUI
                packet, address = udp_socket.recvfrom(buffer)
                
                sequence_number_bytes = packet[:4]  # Extrai apenas os 4 primeiros bytes
                checksum_recebido = int.from_bytes(packet[4:8], byteorder='big')
                checkum = calcular_checksum(packet[8:])                                
                sequence_number = int.from_bytes(sequence_number_bytes, byteorder='big')

                if  'eof'.encode('utf8') in packet[4:] and len(packet) < 80:                    
                    break

                if sequence_number == numero_sequencia_esperado and checksum_recebido == checkum:
                    print(f"recebido {sequence_number} {numero_sequencia_esperado}")
                    arquivo.write(packet[8:])                    
                    tempo_final = time()
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
            N = 10
            tempo_chegada = [0 for x in range(N)]
            tempo = [0 for x in range(N)]
            window_size_inicial = N  # Define o tamanho da janela
            window_start = 0  # Começa a janela em 0
            #threshold = 8  # Define o limite de reenvio do payload 
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

                    indice = numero_sequencia_base if numero_sequencia_base < N else N - 1
                    if tempo[indice] > 2: #TODO verificar esse tempo 0.6s
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


def main():
    USUARIO = "admin"
    SENHA = "admin"
    try:
        servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        servidor_socket.bind((HOST, PORTA_UDP))

        while True:
            print(f"Servidor ouvindo em {HOST}:{PORTA_UDP}")
            mensagem, endereco_cliente = servidor_socket.recvfrom(1024)
            descartar = mensagem.isdigit()
            
            if not descartar:
                funcao, nome_arquivo = mensagem.decode().split(" ", 1)
                
                if funcao == "listar":
                    mensagem_inicial = "\n".join(listar_arquivos())
                    servidor_socket.sendto(mensagem_inicial.encode(), endereco_cliente)

                elif funcao == "download":
                    enviar_arquivo(nome_arquivo, endereco_cliente, servidor_socket)

                elif funcao == "upload":
                    receber_arquivo(servidor_socket, nome_arquivo)
                    pass
                elif funcao == "auth":
                    usuario, senha = nome_arquivo.split("|")
                    print(f"Autenticando {usuario}    {senha}...")
                    
                    if USUARIO == usuario and SENHA == senha:
                        servidor_socket.sendto("ok".encode(), endereco_cliente)
                    else:
                        servidor_socket.sendto("fail".encode(), endereco_cliente)
                else:
                    print("Função inválida.")

            else:
                print("Pacote descartado.")

    except KeyboardInterrupt:
        print("\nEncerrando socket do servidor.")
        servidor_socket.close()
    except ConnectionResetError:
        print(f"Conexão com {endereco_cliente} foi encerrada pelo cliente.")
        servidor_socket.close()
    finally:
        servidor_socket.close()


if __name__ == "__main__":
    main()