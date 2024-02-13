import socket
import json

request = {
    "requestType": 4,
    "userID": 1,
    "firstName": "ido",
    "lastName": "sigler",
    "email": "edosigler3@gmail.com",
    "rank": "admin",
    "fileID": 1,
    "fileName": "admin.exe"
}
jsonDump = json.dumps(request)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 6987))
s.send(jsonDump.encode())

print(s.recv(1024))
