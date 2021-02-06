import json
from flask import Flask, request, abort, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
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


class Location(db.Model):
    name = db.Column(db.String(64), primary_key=True, nullable=False)
    items = db.relationship('StorageItem', back_populates='location')


class StorageItem(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.name'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.handle'))

    location = db.relationship('Location', back_populates='items')
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

    except (KeyError, ValueError, TypeError, IntegrityError):
        if ValueError:
            abort(400, "Weight and price must be numbers")
        elif KeyError:
            abort(400, "Incomplete request - missing fields")
        elif TypeError:
            abort(415, "Request content type must be JSON")
        else:
            abort(400)


@app.route("/storage/<product>/add/", methods=["POST", "GET", "PUT", "DELETE"])
def add_to_storage(product):
    try:
        if not request.json:
            abort(415, "Request content type must be JSON")
        if request.method not in "POST":
            abort(405, "POST method required")

        location_name = request.json["location"]
        prod = Product.query.filter_by(handle=product).first()
        location = Location.query.filter_by(name=location_name).first()
        quantity = int(request.json["qty"])

        if prod:
            if location:
                item = StorageItem(
                    qty=quantity,
                    location_id=location.name,
                    product=prod
                )
                db.session.add(item)
                db.session.commit()
                location.items.append(item)
                db.session.commit()
                return Response(status=201)

            location = Location(name=location_name)
            item = StorageItem(
                qty=quantity,
                location_id=location.name,
                product=prod
            )
            location.items.append(item)
            db.session.commit()
            return Response(status=201)
        else:
            abort(404, "Product not found.")

    except (KeyError, ValueError, IntegrityError):
        if ValueError:
            abort(400, "Qty must be an integer")
        elif KeyError:
            abort(400, "Incomplete request - missing fields")
        else:
            abort(400)


@app.route("/storage/", methods=["POST", "GET", "PUT", "DELETE"])
def get_inventory():
    try:
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
                store_tuple = [item.location.name, item.qty]
                dict_product['inventory'].append(store_tuple)
            product_list.append(dict_product)
        return json.dumps(product_list)
    except(KeyError, ValueError, IntegrityError):
        if ValueError:
            abort(400, "Qty must be an integer")
        elif KeyError:
            abort(400, "Incomplete request - missing fields")
        else:
            abort(400)
