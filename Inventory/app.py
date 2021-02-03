from flask import Flask, request, abort
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


class Storage(db.Model):
    location = db.Column(db.String(32), primary_key=True, nullable=False)
    qty = db.Column(db.Integer)
    product_handle = db.Column(db.String(128), db.ForeignKey("product.handle"), unique=True, )

    product = db.relationship("Product", back_populates="storage", uselist=False)


class Product(db.Model):
    handle = db.Column(db.String(128), primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    storage = db.relationship("Storage", back_populates="product")


@app.route("/products/add/", methods=["POST"])
def add_product():
    try:
        print(request)
        print(request.json)
        if request.method not in "POST":
            abort(405, "POST method required")
        handleStr = request.json["handle"]
        handleCheck = False #Product.query.filter_by(handle=handleStr).first()
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
            return prod
        else:
            abort(409, "Handle already exists")

    except (KeyError, ValueError, IntegrityError):
        if ValueError:
            abort(400, "Weight and price must be numbers")
        if KeyError:
            abort(400, "Incomplete request - missing fields")
    abort(400)


@app.route("/storage/<product>/add/", methods=["POST"])
def add_to_storage(product):
    try:
        if request.method not in "POST":
            abort(405, "POST method required")
        prod = Product.query.filter_by(handle=product).first()
        if prod:
            loc = request.json["location"]
            qty = int(request.json["qty"])
            store = Storage.query.filter_by(location=loc).first()

            store.product = prod
            store.qty = qty
            prod.storage.append(store)
            db.session.commit()
            return prod
        else:
            abort(404, "Product not found.")
    except (KeyError, ValueError, IntegrityError):
        if ValueError:
            abort(400, "Qty must be an integer")
        if KeyError:
            abort(400, "Incomplete request - missing fields")
    abort(400)
