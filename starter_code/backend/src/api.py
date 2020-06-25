import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

###############################################
# ROUTES
###############################################


'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks", methods=["GET"])
def get_drinks():
    try:
        drinks = [
            drink.short() for drink in Drink.query.all()
        ]
        return jsonify({
            "drinks": drinks
        })
    except Exception:
        abort(400)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=["GET"])
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(jwt):
    try:
        drinks = [
            drink.long() for drink in Drink.query.all()
        ]
        return jsonify({
            "success": True,
            "drinks": drinks
        })
    except AuthError as authErr:
        abort(401, authErr)
    except Exception:
        abort(500)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure

    Example Request: {"id":-1,"title":"",
        "recipe":[{"name":"","color":"white","parts":1}]}
'''


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drink(jwt):
    try:
        data = json.loads(request.data)
        title = data["title"]
        recipe = data["recipe"]
        # Validate drink title is specified
        if (title is None) or (len(title.strip()) == 0):
            abort(400, "Drink title not specified")

        # Validate atleast one recipe is specified
        if (not isinstance(recipe, list)) or (len(recipe) == 0):
            abort(400, "Drink recipe not specified")

        # Validate each recipe
        for r in recipe:
            if (r["color"] is None or r["name"] is None or r["parts"] is None):
                abort(400, "Invalid drink recipe configuration")

        recipe_str = json.dumps(recipe)
        new_drink = Drink()
        new_drink.title = title
        new_drink.recipe = recipe_str
        new_drink.insert()

        return jsonify({
            "success": True,
            "drinks": [
                new_drink.long()
            ]
        })
    except Exception as err:
        abort(500, err)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(jwt, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(400, "Invalid drink id")

        data = json.loads(request.data)
        title = data["title"]
        recipe = data["recipe"]
        # Validate drink title is specified
        if (title is None) or (len(title.strip()) == 0):
            abort(400, "Drink title not specified")

        # Validate atleast one recipe is specified
        if (not isinstance(recipe, list)) or (len(recipe) == 0):
            abort(400, "Drink recipe not specified")

        # Validate each recipe
        for r in recipe:
            if (r["color"] is None or r["name"] is None or r["parts"] is None):
                abort(400, "Invalid drink recipe configuration")

        recipe_str = json.dumps(recipe)
        drink.title = title
        drink.recipe = recipe_str
        drink.update()

        return jsonify({
            "success": True,
            "drinks": [
                drink.long()
            ]
        })
    except Exception as err:
        abort(500, err)


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
        returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(jwt, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(400, "Drink not found")

        drink.delete()

        return jsonify({
            "success": True
        })
    except Exception as err:
        abort(500, err)


###########################################
# Error Handling
###########################################


@app.errorhandler(500)
def internalServerError(error):
    return jsonify({
        "success": False,
        "error": 500,
        "code": "internal_server_error",
        "message": "Internal server error",
        "description": error
    }), 500


'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad Request."
    }), 400


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''


'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
def resourceNotFound(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    error = jsonify(ex.error)
    return jsonify({
        "success": False,
        "error": ex.status_code,
        "code": ex.error.get("code"),
        "message": ex.error.get("description")
    }), ex.status_code
