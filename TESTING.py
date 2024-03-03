import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("0.0.0.0", 11111))
s.listen(1)
c, addr = s.accept()

print(c.recv(2))