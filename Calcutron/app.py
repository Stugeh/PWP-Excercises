from flask import Flask, request
import math

app = Flask("Hello")


@app.route("/")
def hello():
    help_string = "<br/>How to:<br /> multipliers: add, sub, mul, div:<br/> http://127.0.0.1:5000/"\
        "(your multiplier)/(number_1)/(number_2)"
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
    if number_2 == 0:
        return "NaN"
    total = number_1 / number_2
    return "total is: " + str(total)


@app.route("/trig/<func>")
def trig(func):
    if func != "sin" and func != "cos" and func != "tan":
        return "Operation not found", 404

    try:
        angle = float(request.args["angle"])
    except KeyError:
        return "Missing query parameter: angle", 400
    except ValueError:
        return "Couldn't parse parameter angle into a float.", 400
    try:
        units = request.args["unit"]
    except KeyError:
        units = "degree"

    if units != "degree" and units != "radian":
        return "Invalid query parameter value(s)", 400

    if units == "degree":
        math.radians(angle)

    if func == "sin":
        return str(round(math.sin(angle), 3))
    if func == "cos":
        return str(round(math.cos(angle), 3))
    if func == "tan":
        return str(round(math.tan(angle), 3))
