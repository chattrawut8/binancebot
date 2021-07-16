from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/webhook', methods=['POST'])
def webhook():
    print(request)
    return request