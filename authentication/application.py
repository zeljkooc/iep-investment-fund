from flask import Flask, request, Response, jsonify
from models import database, User, UserRole, Role
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from configuration import Configuration
import re


application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)

@application.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        data = {}

    # Provera postojanja polja u JSON-u
    if "forename" not in data or data["forename"] is None or not isinstance(data["forename"], str) or len(data["forename"]) == 0:
        return jsonify({"message": "Field forename is missing."}), 400

    if "surname" not in data or data["surname"] is None or not isinstance(data["surname"], str) or len(data["surname"]) == 0:
        return jsonify({"message": "Field surname is missing."}), 400

    if "email" not in data or data["email"] is None or not isinstance(data["email"], str) or len(data["email"]) == 0:
        return jsonify({"message": "Field email is missing."}), 400

    if "password" not in data or data["password"] is None or not isinstance(data["password"], str) or len(data["password"]) == 0:
        return jsonify({"message": "Field password is missing."}), 400

    forename = data["forename"]
    surname = data["surname"]
    email = data["email"]
    password = data["password"]

    # Provera formata email adrese i dužine
    if len(email) > 256 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
        return jsonify({"message": "Invalid email."}), 400

    # Provera dužine lozinke
    if len(password) < 8 or len(password) > 256:
        return jsonify({"message": "Invalid password."}), 400

    # Provera da li email već postoji u bazi
    existing_user = database.session.execute(
        database.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if existing_user is not None:
        return jsonify({"message": "Email already exists."}), 400

    employee_role = database.session.execute(
        database.select(Role).where(Role.name == "employee")
    ).scalar_one_or_none()

    if employee_role is None:
        return jsonify({"message": "Employee role not found."}), 500

    user = User(
        email=email,
        password=password,
        forename=forename,
        surname=surname
    )

    database.session.add(user)
    database.session.flush()

    user_role = UserRole(
        userId=user.id,
        roleId=employee_role.id
    )

    database.session.add(user_role)
    database.session.commit()

    return jsonify({}), 200


@application.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        data = {}

    if "email" not in data or data["email"] is None or not isinstance(data["email"], str) or len(data["email"]) == 0:
        return jsonify({"message": "Field email is missing."}), 400

    if "password" not in data or data["password"] is None or not isinstance(data["password"], str) or len(data["password"]) == 0:
        return jsonify({"message": "Field password is missing."}), 400

    email = data["email"]
    password = data["password"]

    if len(email) > 256 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
        return jsonify({"message": "Invalid email."}), 400

    user = database.session.execute(
        database.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user is None or user.password != password:
        return jsonify({"message": "Invalid credentials."}), 400

    # Dohvatanje svih uloga korisnika direktno iz baze upitom nad tabelom Role
    roles_db = database.session.execute(
        database.select(Role)
        .join(UserRole, UserRole.roleId == Role.id)
        .where(UserRole.userId == user.id)
    ).scalars().all()

    roles_list = [r.name for r in roles_db] if roles_db else ["employee"]

    access_token = create_access_token(
        identity=user.email,
        additional_claims={
            "forename": user.forename,
            "surname": user.surname,
            "role": roles_list,
            "email": user.email
        }
    )

    return jsonify({"accessToken": access_token}), 200


@application.route('/delete', methods=['POST'])
@jwt_required()
def delete_user():
    current_user_email = get_jwt_identity()

    user = database.session.execute(
        database.select(User).where(User.email == current_user_email)
    ).scalar_one_or_none()

    if user is None:
        return jsonify({"message": "Unknown user."}), 400

    database.session.execute(
        database.delete(UserRole).where(UserRole.userId == user.id)
    )

    database.session.delete(user)
    database.session.commit()

    return jsonify({}), 200

@application.route('/check', methods=['POST'])
@jwt_required()
def check():
    return "Token is valid!"


@application.route('/', methods=['GET'])
def index():
    return "Hello World!"


if __name__ == "__main__":
    application.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )