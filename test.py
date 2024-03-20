import requests
import json

pa = {"user": json.dumps({"userID": 1, "firstName": "niga", "lastName": "hgt", "email":"asdfasdfasd", "rank": "niga"})}

r = requests.get("http://127.0.0.1:15674/pieceData", params=pa)

print(r.text)