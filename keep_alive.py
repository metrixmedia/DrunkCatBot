from flask import Flask
from threading import Thread
import random


app = Flask('')

@app.route('/')
def main():
    return "Le bot est disponible pour l'instant ! Le serveur WebSocket est à présent disponible. CODE HTTPS : 200 OK UP"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()