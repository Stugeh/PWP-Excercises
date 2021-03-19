import json
from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from sqlalchemy.engine import Engine
from sqlalchemy import event

app = Flask(__name__)
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


# class StorageEntry(db.Model):
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
    def product_check(self, prod_handle):
        result = Product.query.filter_by(handle=prod_handle).first()
        if not result:
            body = MasonBuilder(resource_url=request.path)
            body.add_error('Not Found', 'No product found by handle: ' + prod_handle)
            return Response(json.dumps(body), status=404, mimetype="application/vnd.mason+json")
        return result

    def get(self, prod_handle):
        if prod_handle is not None:
            result = self.product_check(prod_handle)
            body = InventoryBuilder(handle=result.handle, weight=result.weight, price=result.price)
            body.add_control_edit_product(result.handle)
            body.add_control_delete_product(result.handle)
            body.add_control("self", api.url_for(self, prod_handle=result.handle))
            body.add_control("profile", "/profiles/product/")
            body.add_control("collection", api.url_for(ProductCollection))
            return Response(json.dumps(body), status=200, mimetype="application/vnd.mason+json")

    def put(self, prod_handle):
        try:
            if not request.json:
                body = MasonBuilder(resource_url=request.path)
                body.add_error('Wrong content type', 'Request must be a json object')

                return Response(json.dumps(body), status=415, mimetype="application/vnd.mason+json")

            if prod_handle is not None:
                product = self.product_check(prod_handle)

                if Product.query.filter_by(handle=request.json['handle']).first() and prod_handle != request.json["handle"]:
                    body = MasonBuilder(resource_url=request.path)
                    body.add_error('Duplicate Key', 'This handle already exists in the database')

                    return Response(json.dumps(body), status=409, mimetype="application/vnd.mason+json")

                product.handle = request.json["handle"]
                product.price = float(request.json['price'])
                product.weight = float(request.json["weight"])
                db.session.commit()
                objectUri = api.url_for(ProductItem, prod_handle=product.handle)

                return Response(status=204, headers={"Location": objectUri}, mimetype='application/json')

        except (KeyError, ValueError):
            body = MasonBuilder(resource_url=request.path)
            body.add_error('Schema validation failed', 'Request didnt match the schema')
            return Response(json.dumps(body), status=400, mimetype="application/vnd.mason+json")

    def delete(self, prod_handle):
        if prod_handle is not None:
            result = self.product_check(prod_handle)
            db.session.delete(result)
            db.session.commit()
            return Response(status=204, mimetype='application/json')


class ProductCollection(Resource):
    def get(self):
        products = Product.query.all()
        body = InventoryBuilder()
        body.add_namespace('inventoryApi', '/api/products/')
        body["items"] = []
        for product in products:
            item = InventoryBuilder(
                handle=product.handle,
                weight=float(product.weight),
                price=float(product.price),
            )
            item.add_control("self", api.url_for(ProductItem, prod_handle=product.handle))
            item.add_control("profile", "/profiles/product/")
            body["items"].append(item)
        body.add_control("self", api.url_for(self))
        body.add_control_add_product()
        body.add_control_all_products()
        return Response(json.dumps(body), status=200, mimetype="application/vnd.mason+json")

    def post(self):
        if not request.json:
            body = MasonBuilder(resource_url=request.path)
            body.add_error('Wrong content type', 'Request must be a json object')

            return Response(json.dumps(body), status=415, mimetype="application/vnd.mason+json")
        try:

            handleStr = request.json["handle"]
            handleCheck = Product.query.filter_by(handle=handleStr).first()
            if handleCheck:
                body = MasonBuilder(resource_url=request.path)
                # LOL
                price = request.json["price"]
                body.add_error('Duplicate Key', 'This handle already exists in the database')
                return Response(json.dumps(body), status=409, mimetype="application/vnd.mason+json")

            prod = Product(
                handle=request.json["handle"],
                price=float(request.json["price"]),
                weight=float(request.json["weight"])
            )
            db.session.add(prod)
            db.session.commit()
            objectUri = api.url_for(ProductItem, prod_handle=prod.handle)
            return Response(status=201, headers={"Location": objectUri}, mimetype='application/json')
        except (KeyError, ValueError):
            body = MasonBuilder(resource_url=request.path)
            body.add_error('Schema validation failed', 'Request didnt match the schema')
            return Response(json.dumps(body), status=400, mimetype="application/vnd.mason+json")


api.add_resource(ProductCollection, '/api/products/')
api.add_resource(ProductItem, '/api/products/<prod_handle>/')


# HYPERMEDIA BUILDERS #

class MasonBuilder(dict):
    def add_error(self, title, details):
        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        if "@namespaces" not in self:
            self["@namespaces"] = {}
        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        if "@controls" not in self:
            self["@controls"] = {}
        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


class InventoryBuilder(MasonBuilder):
    @staticmethod
    def item_schema():
        schema = {
            "type": "object",
            "required": ["handle", "weight", "price"]
        }
        props = schema["properties"] = {}
        props["handle"] = {
            "type": "string"
        }
        props["weight"] = {
            "type": "number"
        }
        props["price"] = {
            "type": "number"
        }
        return schema

    def add_control_all_products(self):
        self.add_control(
            "storage:products-all",
            href='/api/products/',
            method="GET"
        )

    def add_control_delete_product(self, handle):
        self.add_control(
            "storage:delete",
            href='/api/products/' + handle + '/',
            method="DELETE"
        )

    def add_control_add_product(self):
        self.add_control(
            "storage:add-product",
            "/api/products/",
            method="POST",
            encoding="json",
            title="Add product",
            schema=self.item_schema()
        )

    def add_control_edit_product(self, handle):
        self.add_control(
            "edit",
            href='/api/products/' + handle + '/',
            method="PUT",
            encoding="json",
            schema=self.item_schema()
        )


@app.route('/api/')
def entry():
    body = InventoryBuilder()
    body.add_namespace('storage', '/api/products/')
    body.add_control_all_products()
    return Response(json.dumps(body), status=200, mimetype="application/vnd.mason+json")

@app.route('/profiles/product/')
def productProf():
    return 'product profile'

# class test():
#     inventory = InventoryBuilder()
#     inventory.add_control_add_product()
#     #inventory.add_control_all_products()
#     print(inventory)







