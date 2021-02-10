import json
from flask import Flask, request, abort, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

app = Flask("inventory")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class StorageItem(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(64), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.handle'))

    product = db.relationship("Product", back_populates="inventory")


class Product(db.Model):
    handle = db.Column(db.String(128), primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    inventory = db.relationship("StorageItem", back_populates="product")


@app.route("/products/add/", methods=["POST", "GET", "PUT", "DELETE"])
def add_product():
    try:
        if not request.json:
            abort(415, "Request content type must be JSON")
        if request.method not in "POST":
            abort(405, "POST method required")
        handleStr = request.json["handle"]
        handleCheck = Product.query.filter_by(handle=handleStr).first()
        if not handleCheck:
            price = float(request.json["price"])
            weight = float(request.json["weight"])
            prod = Product(
                handle=handleStr,
                price=price,
                weight=weight
            )
            db.session.add(prod)
            db.session.commit()
            return Response(status=201)
        abort(409, "Handle already exists")

    except KeyError:
        abort(400, "Incomplete request - missing fields")
    except ValueError:
        abort(400, "Weight and price must be numbers")
    except TypeError:
        abort(415, "Request content type must be JSON")


@app.route("/storage/<product>/add/", methods=["POST", "GET", "PUT", "DELETE"])
def add_to_storage(product):
    try:
        if not request.json:
            abort(415, "Request content type must be JSON")
        if request.method not in "POST":
            abort(405, "POST method required")

        location_name = request.json["location"]
        prod = Product.query.filter_by(handle=product).first()
        quantity = int(request.json["qty"])
        if prod:
            item = StorageItem(
                qty=quantity,
                location=location_name,
                product=prod
            )
            db.session.add(item)
            db.session.commit()
            db.session.commit()
            return Response(status=201)
        abort(404, "Product not found.")

    except ValueError:
        abort(400, "Qty must be an integer")
    except KeyError:
        abort(400, "Incomplete request - missing fields")


@app.route("/storage/", methods=["POST", "GET", "PUT", "DELETE"])
def get_inventory():
    try:
        if request.method not in "GET":
            abort(405, "GET method required")
        products = Product.query.all()
        product_list = []
        for product in products:
            dict_product = {
                'handle': product.handle,
                'weight': product.weight,
                'price': product.price,
                'inventory': []
            }
            for item in product.inventory:
                store_tuple = [item.location, item.qty]
                dict_product['inventory'].append(store_tuple)
            product_list.append(dict_product)
        return json.dumps(product_list)

    except ValueError:
        abort(400, "Qty must be an integer")
    except KeyError:
        abort(400, "Incomplete request - missing fields")
