import socket, select, traceback, queue
import os
import threading
from dotenv import load_dotenv
from numpy import random
import zlib
from time import sleep, time
from client_server_utils import listar_arquivos, enviar_arquivo, receber_arquivo, calcular_md5

load_dotenv()
dir = os.path.dirname(__file__)
server_files_path = os.path.join(dir, os.environ.get("SERVER_FILES_PATH"))
HOST = os.environ.get("SERVER_HOST")
PORTA_UDP = int(os.environ.get("UDP_PORT"))


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
                    
                elif funcao == "auth":
                    usuario, senha = nome_arquivo.split("|")
                    #print(f"Autenticando usuario: {usuario}")
                    
                    if USUARIO == usuario and SENHA == senha:
                        servidor_socket.sendto("ok".encode(), endereco_cliente)
                    else:
                        servidor_socket.sendto("fail".encode(), endereco_cliente)
                        
                elif funcao == "nofile":
                    print(f"Arquivo {nome_arquivo} inexistente.")
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
