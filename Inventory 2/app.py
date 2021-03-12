from flask import Flask, request, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from sqlalchemy.engine import Engine
from sqlalchemy import event

app = Flask("inventory")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

api = Api(app)


# SCHEMAS #
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# class StorageItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True, nullable=False)
#     qty = db.Column(db.Integer, nullable=False)
#     location = db.Column(db.String(64), nullable=False)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.handle'))
#
#     product = db.relationship("Product", back_populates="inventory")


class Product(db.Model):
    handle = db.Column(db.String(128), primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)


# RESOURCES #
class ProductItem(Resource):

    def get(self, prod_handle):
        if prod_handle is not None:
            result = Product.query.filter_by(handle=prod_handle).first()
            if not result:
                abort(404, message='no product by that handle')
            return result
        abort(400, "Incomplete request - missing prod_handle")


class Inventory(Resource):

    def get(self):
        try:
            products = Product.query.all()
            product_list = []
            for product in products:
                dict_product = {
                    'handle': product.handle,
                    'weight': product.weight,
                    'price': product.price,
                }
                product_list.append(dict_product)
            return product_list
        except ValueError:
            abort(400, "Qty must be an integer")
        except KeyError:
            abort(400, "Incomplete request - missing fields")

    def post(self):
        if not request.json:
            abort(415)
        try:
            handleStr = request.json["handle"]
            handleCheck = Product.query.filter_by(handle=handleStr).first()
            if not handleCheck:
                prod = Product(
                    handle=request.json["handle"],
                    price=float(request.json["price"]),
                    weight=float(request.json["weight"])
                )
                db.session.add(prod)
                db.session.commit()
                objectUri = api.url_for(ProductItem, prod_handle=prod.handle)
                return Response(status=201, headers={"Location": objectUri}, mimetype='application/json')
            abort(409)
        except KeyError:
            abort(400, "Incomplete request - missing fields")
        except ValueError:
            abort(400, "Weight and price must be numbers")
        except TypeError:
            abort(415, "Request content type must be JSON")


api.add_resource(Inventory, '/api/products/')
api.add_resource(ProductItem, '/api/products/<prod_handle>/')