from flask import Flask

app = Flask("Hello")


@app.route("/")
def hello():
    help_string = "How to:<br /> multipliers: add, sub, mul, div: http://127.0.0.1:5000/(your multiplier)/(" \
                  "float:number_1)/(float:number_2)"
    return help_string


@app.route("/add/<float:number_1>/<float:number_2>")
def addition(number_1, number_2):
    total = number_1 + number_2
    return "total is: " + str(total)


@app.route("/sub/<float:number_1>/<float:number_2>")
def subtraction(number_1, number_2):
    total = number_1 - number_2
    return "total is: " + str(total)


@app.route("/mul/<float:number_1>/<float:number_2>")
def multiplication(number_1, number_2):
    total = number_1 * number_2
    return "total is: " + str(total)


@app.route("/div/<float:number_1>/<float:number_2>")
def division(number_1, number_2):
    total = number_1 / number_2
    if number_2 == 0:
        return "NaN"
    return "total is: " + str(total)
