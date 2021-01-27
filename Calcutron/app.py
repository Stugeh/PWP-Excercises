from flask import Flask

app = Flask("Hello")

@app.route("/")
def hello():
    return "How to"