import socket
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# Configurações do servidor
dir = os.path.dirname(__file__)
files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST_")
PORTA_TCP = int(os.environ.get("TCP_PORT"))
PORTA_UDP = int(os.environ.get("UDP_PORT"))

# Função para listar os arquivos no diretório do servidor
def listar_arquivos():
    return os.listdir(files_path)

# Função para enviar um arquivo para o cliente usando UDP
def enviar_arquivo(nome_arquivo, endereco_cliente, porta_cliente):
    try:
        with open(os.path.join(files_path, nome_arquivo), 'rb') as arquivo:
            cliente_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket.setdefaulttimeout(5)

            initial_window_size = 4  # Define o tamanho da janela
            window_start = 0  # Começa a janela em 0
            threshold = 8  # Define o limite de reenvio do payload
            sending_retry = 0

            while True:
                # Calcula o restante de bytes a serem enviados
                remaining_bytes = os.path.getsize(os.path.join(files_path, nome_arquivo)) - window_start
                print(f"Remaining bytes: {remaining_bytes}")
                # Ajusta o tamanho da janela se ultrapassar o limite
                window_size = min(initial_window_size, remaining_bytes)

                if window_size <= 0:
                    break
                #window_end = min(window_start + window_size, os.path.getsize(os.path.join(files_path, nome_arquivo)))
                
                window_end = window_start + window_size
                print(f"Window start: {window_start}, Window end: {window_end}, Window size: {window_size}")
                sent_packets = []
                for i in range(window_start, window_end):

                    arquivo.seek(i * 1024)  # Move o ponteiro do arquivo para o byte correspondente
                    packet = bytearray()
                    packet.extend(i.to_bytes(4, byteorder='big'))  # Adiciona o numero de sequência ao pacote
                    packet.extend(arquivo.read(1024))  

                    #print(f"Enviando payload {i}")
                    cliente_udp_socket.sendto(packet, (endereco_cliente, porta_cliente))
                    sent_packets.append(i)

                ack_received = False
                final_ack_received = False
                while not ack_received and not final_ack_received:
                    try:
                        ack, _ = cliente_udp_socket.recvfrom(1024)
                        ack_number = int(ack.decode())

                        if ack_number == -1:
                            final_ack_received = True

                        if ack_number == window_end:
                            window_start += window_size
                            ack_received = True
                            print(f"ACK {ack_number} Recebido. Reenviando os pacotes.")
                        
                    except socket.timeout:
                        print(f"Timeout aconteceu. Reenviando os pacotes {sending_retry}.")
                        sending_retry += 1
                        
                        """ for seq_num in sent_packets:
                            arquivo.seek(seq_num * 1024)
                            packet = bytearray()
                            packet.extend(seq_num.to_bytes(4, byteorder='big'))
                            packet.extend(arquivo.read(1024))
                            print(f"Retransmitindo payload {seq_num}")
                            cliente_udp_socket.sendto(packet, (endereco_cliente, porta_cliente)) """

                        break  # Reenvia os pacotes
                    

                    if initial_window_size < threshold:
                        initial_window_size *= 2  # Slow start
                    else:
                        initial_window_size += 1  # Congestion avoidance 
                    #initial_window_size += 1 

                if final_ack_received:
                    break
                if window_start >= os.path.getsize(os.path.join(files_path, nome_arquivo)):
                    break  # Todos os pacotes foram enviados

            cliente_udp_socket.close()
            print(f"Enviado o arquivo {nome_arquivo} para {endereco_cliente}")
    except FileNotFoundError:
        print(f"Arquivo {nome_arquivo} não encontrado no servidor.")
        cliente_udp_socket.close()

# Função para lidar com as solicitações de um cliente
def lidar_com_cliente(conexao, endereco_cliente):
    try:
        #get_network_status(conexao, endereco_cliente)
        # Envia a lista de arquivos para o cliente
        arquivos_disponiveis = listar_arquivos()
        mensagem_inicial = "\n".join(arquivos_disponiveis)
        conexao.sendall(mensagem_inicial.encode())

        # Loop para lidar com as solicitações do cliente
        while True:
            # Recebe a solicitação do cliente para download usando UDP
            nome_arquivo = conexao.recv(4096).decode()

            if not nome_arquivo:
                break  # Cliente encerrou a conexão

            # Envia o arquivo usando UDP
            enviar_arquivo(nome_arquivo, endereco_cliente[0], PORTA_UDP)
            
    except ConnectionResetError:
        print(f"Conexão com {endereco_cliente} foi encerrada pelo cliente.")

    finally:
        # Fecha a conexão TCP
        conexao.close()


#Function to get the network status from the client, the delay and the connection bandwidth
def get_network_status(client_socket, client_address):
    # get client download speed
    print(f"Connection from {client_address}")
    
    start_time = time.time()
    
    data = client_socket.recv(1024)
    
    end_time = time.time()
    connection_delay = end_time - start_time
    
    download_speed = len(data) / connection_delay
    
    connection_delay_variable = connection_delay
    download_speed_variable = download_speed
    
    print(f"Connection delay: {connection_delay} seconds")
    print(f"Download speed: {download_speed} bytes/second")
    

# Criação do socket TCP do servidor
servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor_socket.bind((HOST, PORTA_TCP))
servidor_socket.listen()

print(f"Servidor ouvindo em {HOST}:{PORTA_TCP}")
print(os.getcwd())
try:

    while True:
        # Aguarda por conexões
        conexao, endereco_cliente = servidor_socket.accept()
        print(f"Conexão estabelecida com {endereco_cliente}")

        # Cria uma thread para lidar com o cliente
        cliente_thread = threading.Thread(target=lidar_com_cliente, args=(conexao, endereco_cliente))
        cliente_thread.start()
        cliente_thread.join()

except KeyboardInterrupt:
    pass

servidor_socket.close()