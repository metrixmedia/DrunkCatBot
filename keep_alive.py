from flask import Flask
from threading import Thread
import random


app = Flask('')

@app.route('/')
def main():
    return "Bot is ONLINE - HTTP/1.1 200 OK"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()