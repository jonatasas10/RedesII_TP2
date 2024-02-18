import socket, select
import os
from dotenv import load_dotenv
from time import time, sleep
from numpy import random
import zlib
import hashlib
import threading
import traceback
import queue
import numpy as np

load_dotenv()

# Configurações do cliente
dir = os.path.dirname(__file__)
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))
client_files_path = os.path.join(dir, os.environ.get("CLIENT_FILES_PATH"))

if __name__ == "__main__":
    print("ARQUIVO UTILITÁRIO, EXECUTE O CLIENTE.PY")

def calcular_md5(arquivo):
    md5_hash = None
    with open(arquivo,'rb') as arquivo:
        arquivo_md5 = arquivo.read()
        md5_hash = hashlib.md5(arquivo_md5).hexdigest()
    return md5_hash

def random_delay():
    random_delay = random.uniform(0.002, 0.03) #atraso entre 10ms - 50ms, ida e volta max 100ms
    sleep(random_delay)

def calcular_checksum(data):
    return zlib.crc32(data)

def velocidade_download(q):
    eof = False
    tempos = []
    pcts = []
    inicio = time()
    while not eof:
        # os.system("clear")
        try:
            tam_pacote, atraso, eof = q.get()
            tempos.append(atraso)
            pcts.append(tam_pacote)

        except: pass
        if (time() - inicio) >= 1:
            inicio = time()
            tam_medio = np.mean(pcts)
            atraso = np.mean(tempos)
            pcts.clear()
            tempos.clear()
            download_speed = tam_medio*8 / (atraso*10**6)
            #print(f"\nDelay de conexão: {round(atraso,2)} segundos")
            print(f"Velocidade de download: {round(download_speed, 2)} Mbps\n")

def receber_arquivo(udp_socket, nome_arquivo):
    global tamanho
    global tempo_pct
    global global_eof
    numero_sequencia_esperado = 0
    buffer = 1500
    tam_arquivo = 0
    tam_final_pacote = 0
    count = 0
    eof = False
    with open(os.path.join(client_files_path, nome_arquivo), 'wb') as arquivo:
        tempo = time()
        q = queue.Queue()
        threading.Thread(target=velocidade_download, args=[q]).start()
        while True:
            try:
                tempo_inicial = time()

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
                tempo_final = time()
                tam_pacote = len(packet[8:]) if eof == False else len(packet[12:])
                #tam_arquivo += tam_pacote
                tam_final_pacote += len(packet) #para cálculo da vazão
                atraso = tempo_final - tempo_inicial
                q.put((tam_pacote, atraso, eof))
                if sequence_number == numero_sequencia_esperado and checksum_recebido == checkum:
                    #print(f"recebido {sequence_number} {numero_sequencia_esperado}")
                    arquivo.write(packet[8:]) if eof == False else arquivo.write(packet[12:])
                    #tempo_final = time()
                    tam_pacote = len(packet[8:]) if eof == False else len(packet[12:])
                    tam_arquivo += tam_pacote
                    #tam_final_pacote += len(packet) #para cálculo da vazão
                    #atraso = tempo_final - tempo_inicial
                    #tamanho = tam_pacote
                    #tempo_pct = atraso
                    #velocidade_download(address, tam_pacote)
                    #q.put((tam_pacote, atraso, eof))
                    #random_delay() # TODO: DELAY AQUI
                    if eof == False:
                        udp_socket.sendto(str(numero_sequencia_esperado).encode(), address)
                    else:
                        udp_socket.sendto("#eof".encode(), address)
                        global_eof = eof
                        break

                    numero_sequencia_esperado += 1


                else:
                    #print(f"Falha {sequence_number} != {numero_sequencia_esperado}")
                    udp_socket.sendto(f"{numero_sequencia_esperado-1}".encode(), address)


            except socket.timeout:
                print("Timeout. Conexão encerrada.")
                break
        tempo_envio = time() - tempo
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

def enviar_arquivo(nome_arquivo, endereco_cliente, servidor_socket):
    try:
        with open(os.path.join(server_files_path, nome_arquivo), 'rb') as arquivo:
            md5_file = calcular_md5(os.path.join(server_files_path, nome_arquivo))
            buffer = 1450
            numero_sequencia_base = 0
            proximo_numero_sequencia = 0
            arquivo.seek(numero_sequencia_base)
            N = 10

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
                        N = N // 2
                        proximo_numero_sequencia =  numero_sequencia_base
                        eof = False

                if eof and resultado_ack == "#eof":
                    break

            servidor_socket.setblocking(True)
            print("Quantidade de pacotes enviados:", quantidade_pct_enviado)
            print("Quantidade de pacotes perdidos:", total_perdidos)
            print(f"Proporção: {round((total_perdidos/quantidade_pct_enviado)*100,2)}%")
            md5_hash = bytearray()
            md5_checksum = calcular_checksum(md5_file.encode())
            md5_hash.extend(b"#checksum")
            md5_hash.extend(md5_checksum.to_bytes(4, byteorder='big'))
            md5_hash.extend(md5_file.encode())
            servidor_socket.sendto(md5_hash, endereco_cliente)

    except FileNotFoundError:
        print(f"Arquivo {nome_arquivo} não encontrado no servidor.")
    except Exception as e:
        print("Algum outro erro:", e)
        traceback.print_exc()

# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(client_files_path)

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
