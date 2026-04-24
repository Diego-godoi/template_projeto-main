import os
import json
import jwt
import datetime

SECRET_KEY = "secret"

sub = {
    "user_id": "1234-5678",
    "scopes": ["Admin"]
}

payload = {
    "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=20),
    "iat": datetime.datetime.now(tz=datetime.timezone.utc),
    "sub": sub,
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print("Token encoded:", token)

try:
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
    print("Success")
except Exception as e:
    print(type(e))
    print("Exception:", e)

