from flask import Flask, request, abort, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event

app = Flask("inventory")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
marsh = Marshmallow(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    items = db.relationship('Storage', back_populates='location')


class Storage(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    location = db.relationship('Location', back_populates='items')
    product = db.relationship("Product", back_populates="inventory", uselist=False)


class Product(db.Model):
    handle = db.Column(db.String(128), primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('storage.id'))
    inventory = db.relationship("Storage", back_populates="product")


class ProductSchema(marsh.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        load_instance = True

    handle = marsh.auto_field()
    weight = marsh.auto_field()
    price = marsh.auto_field()
    inventory = marsh.auto_field()


class StorageSchema(marsh.SQLAlchemyAutoSchema):
    class Meta:
        model = Storage
        load_instance = True

    location = marsh.auto_field()


class LocationSchema(marsh.SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        load_instance = True

    name = marsh.auto_field()


@app.route("/products/add/", methods=["POST", "GET", "PUT", "DELETE"])
def add_product():
    try:
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
        else:
            abort(409, "Handle already exists")

    except (KeyError, ValueError, IntegrityError):
        if ValueError:
            abort(400, "Weight and price must be numbers")
        elif KeyError:
            abort(400, "Incomplete request - missing fields")
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
                item = Storage(
                    qty=quantity,
                    location_id=location.id,
                    product=prod
                )
                db.session.add(item)
                db.session.commit()
                location.items.append(item)
                db.session.commit()
            else:
                location = Location(name=location_name)
                item = Storage(
                    qty=quantity,
                    location_id=location.id,
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
        product_schema = ProductSchema(many=True)
        product_list = jsonify(product_schema.dump(products))
        print(product_list)
        return product_list

    except(KeyError, ValueError, IntegrityError):
        if ValueError:
            abort(400, "Qty must be an integer")
        elif KeyError:
            abort(400, "Incomplete request - missing fields")
        else:
            abort(400)
