import hashlib
import socket
import os
import time
from dotenv import load_dotenv

dir = os.path.dirname(__file__)

class FileTransferClient:
    def __init__(self):
        load_dotenv()
        self.HOST = os.environ.get("SERVER_HOST")
        self.PORTA_TCP = int(os.environ.get("TCP_PORT"))
        self.PORTA_UDP = int(os.environ.get("UDP_PORT"))
        self.client_files_path = os.path.join(dir, os.environ.get("CLIENT_FILES_PATH"))

    def receber_arquivo(self, nome_arquivo):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('0.0.0.0', self.PORTA_UDP))

        udp_socket.settimeout(5)
        expected_sequence_number = 0

        with open(os.path.join(self.client_files_path, nome_arquivo), 'wb') as arquivo:
            while True:
                try:
                    packet, address = udp_socket.recvfrom(1024*8)
                    sequence_number_bytes = packet[:4]
                    sequence_number = int.from_bytes(sequence_number_bytes, byteorder='big')

                    if sequence_number == expected_sequence_number:
                        arquivo.write(packet[4:])
                        ack = str(sequence_number+1)
                        udp_socket.sendto(ack.encode(), address)
                        expected_sequence_number += 1
                    else:
                        print(f"Falha {sequence_number}!={expected_sequence_number}")
                except socket.timeout:
                    print("Timeout. Conexão encerrada.")
                    break

 
        print(f"Arquivo {nome_arquivo} recebido.")
            
        ack = str(-1)
        udp_socket.sendto(ack.encode(), address)
        udp_socket.close()
    
    def calculate_file_hash(path):
        with open(path, 'rb') as file_to_check:
            data = file_to_check.read()    
            md5_calculation = hashlib.md5(data).hexdigest()

        return md5_calculation


class FileTransferServer:
    def __init__(self):
        load_dotenv()
        self.HOST = os.environ.get("SERVER_HOST")
        self.PORTA_TCP = int(os.environ.get("TCP_PORT"))
        self.PORTA_UDP = int(os.environ.get("UDP_PORT"))
        self.server_files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))

    def handle_client(self, conexao, endereco_cliente):
        try:
            arquivos_disponiveis = self.list_files()
            mensagem_inicial = "\n".join(arquivos_disponiveis)
            conexao.sendall(mensagem_inicial.encode())

            while True:
                nome_arquivo = conexao.recv(4096).decode()

                if not nome_arquivo:
                    break

                self.send_file(nome_arquivo, endereco_cliente[0], self.PORTA_UDP)
                
        except ConnectionResetError:
            print(f"Conexão com {endereco_cliente} foi encerrada pelo cliente.")

        finally:
            conexao.close()

    def get_network_status(self, client_socket, client_address):
        print(f"Connection from {client_address}")

        start_time = time.time()

        data = client_socket.recv(1024)

        end_time = time.time()
        connection_delay = end_time - start_time

        download_speed = len(data) / connection_delay
        print(f"Connection delay: {connection_delay} seconds")
        print(f"Download speed: {download_speed} bytes/second")
    
    def list_files(self):
        return os.listdir(self.server_files_path)

    def calculate_file_hash(path):
        with open(path, 'rb') as file_to_check:
            data = file_to_check.read()    
            md5_calculation = hashlib.md5(data).hexdigest()

        return md5_calculation
    
    def send_file(self, nome_arquivo, endereco_cliente, porta_cliente):

        calculated_file_hash = self.calculate_file_hash(os.path.join(self.server_files_path, nome_arquivo))

        try:
            with open(os.path.join(self.server_files_path, nome_arquivo), 'rb') as arquivo:
                
                cliente_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                socket.setdefaulttimeout(5)

                #envia o checksum do nome do arquivo
                cliente_udp_socket.sendto(calculated_file_hash.encode(), (endereco_cliente, porta_cliente))

                initial_window_size = 4
                window_start = 0
                threshold = 8
                sending_retry = 0

                while True:
                    remaining_bytes = os.path.getsize(os.path.join(self.server_files_path, nome_arquivo)) - window_start
                    window_size = min(initial_window_size, remaining_bytes)

                    if window_size <= 0:
                        break

                    window_end = window_start + window_size

                    sent_packets = []
                    for i in range(window_start, window_end):
                        arquivo.seek(i * 1024)
                        packet = bytearray()
                        packet.extend(i.to_bytes(4, byteorder='big'))
                        packet.extend(arquivo.read(1024))
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

                                if initial_window_size < threshold:
                                    initial_window_size *= 2
                                else:
                                    initial_window_size += 1

                                ack_received = True
                                print(f"ACK {ack_number} Recebido. Enviando outros pacotes.")
                            
                        except socket.timeout:
                            print(f"Timeout aconteceu. Reenviando os pacotes {sending_retry}.")
                            break

                    if final_ack_received:
                        break

                    if window_start >= os.path.getsize(os.path.join(self.server_files_path, nome_arquivo)):
                        break

                cliente_udp_socket.close()
                print(f"Enviado o arquivo {nome_arquivo} para {endereco_cliente}")
        except FileNotFoundError:
            print(f"Arquivo {nome_arquivo} não encontrado no servidor.")
            cliente_udp_socket.close()
