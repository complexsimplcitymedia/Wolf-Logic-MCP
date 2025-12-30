import socket

def get_hostname():
    print(socket.gethostname())

if __name__ == '__main__':
    get_hostname()
