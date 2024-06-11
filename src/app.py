# app.py
"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import db, User, Planet, Character, Favorite
from api.admin import setup_admin
from api.commands import setup_commands
from flask import Blueprint
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

def construct_api_blueprint():
    api = Blueprint('api', __name__)

    @api.route('/users', methods=['GET'])
    def get_all_users():
        users = User.query.all()
        serialized_users = [user.serialize() for user in users]
        return jsonify(serialized_users), 200

    @api.route('/users/favorites', methods=['GET'])
    @jwt_required()
    def get_user_favorites():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        favorites = Favorite.query.filter_by(user_id=user_id).all()
        serialized_favorites = [favorite.serialize() for favorite in favorites]
        return jsonify(serialized_favorites), 200

    @api.route('/users/<int:user_id>/favorites/planets', methods=['POST'])
    @jwt_required()
    def add_favorite_planet(user_id):
        planet_id = request.json.get("planet_id", None)
        if not planet_id:
            return jsonify({"message": "Missing planet_id in request body"}), 400

        planet = Planet.query.get(planet_id)
        if not planet:
            return jsonify({"message": "Planet not found"}), 404

        favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
        if favorite:
            return jsonify({"message": "Planet is already a favorite"}), 400

        new_favorite = Favorite(user_id=user_id, planet_id=planet_id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({"message": "Planet added to favorites"}), 201

    @api.route('/users/<int:user_id>/favorites/characters/<int:character_id>', methods=['POST'])
    @jwt_required()
    def add_favorite_character(user_id, character_id):
        character = Character.query.get(character_id)
        if not character:
            return jsonify({"message": "Character not found"}), 404

        favorite = Favorite.query.filter_by(user_id=user_id, character_id=character_id).first()
        if favorite:
            return jsonify({"message": "Character is already a favorite"}), 400

        new_favorite = Favorite(user_id=user_id, character_id=character_id)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({"message": "Character added to favorites"}), 201

    @api.route('/users/<int:user_id>/favorites/planets/<int:planet_id>', methods=['DELETE'])
    @jwt_required()
    def delete_favorite_planet(user_id, planet_id):
        favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
        if not favorite:
            return jsonify({"message": "Planet is not a favorite"}), 400

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({"message": "Planet removed from favorites"}), 200

    @api.route('/users/<int:user_id>/favorites/characters/<int:character_id>', methods=['DELETE'])
    @jwt_required()
    def delete_favorite_character(user_id, character_id):
        favorite = Favorite.query.filter_by(user_id=user_id, character_id=character_id).first()
        if not favorite:
            return jsonify({"message": "Character is not a favorite"}), 400

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({"message": "Character removed from favorites"}), 200

    @api.route('/planets', methods=['GET'])
    def get_all_planets():
        planets = Planet.query.all()
        serialized_planets = [planet.serialize() for planet in planets]
        return jsonify(serialized_planets), 200

    @api.route('/planets/<int:planet_id>', methods=['GET'])
    def get_planet(planet_id):
        planet = Planet.query.get(planet_id)
        if not planet:
            return jsonify({"message": "Planet not found"}), 404
        return jsonify(planet.serialize()), 200

    @api.route('/characters', methods=['GET'])
    def get_all_characters():
        characters = Character.query.all()
        serialized_characters = [character.serialize() for character in characters]
        return jsonify(serialized_characters), 200

    @api.route('/characters/<int:character_id>', methods=['GET'])
    def get_character(character_id):
        character = Character.query.get(character_id)
        if not character:
            return jsonify({"message": "Character not found"}), 404
        return jsonify(character.serialize()), 200

    @api.route('/login', methods=['POST'])
    def login():
        username = request.json.get("username", None)
        password = request.json.get("password", None)
        user = User.query.filter_by(username=username, password=password).first()
        if not user:
            return jsonify({"message": "Bad username or password"}), 401

        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)

    return api


ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

# database condiguration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)

# Create the api blueprint after initializing db and other dependencies
api = construct_api_blueprint()
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
