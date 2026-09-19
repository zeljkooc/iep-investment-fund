from flask import Flask
from configuration import Configuration
from models import database, Role, UserRole, User
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"])

database.init_app(application)

with application.app_context():
    database.create_all()

    directorRole = Role.query.filter_by(name="director").first()
    if not directorRole:
        directorRole = Role(name="director")
        database.session.add(directorRole)

    employeeRole = Role.query.filter_by(name="employee").first()
    if not employeeRole:
        employeeRole = Role(name="employee")
        database.session.add(employeeRole)

    database.session.commit()

    director = User.query.filter_by(email="onlymoney@gmail.com").first()
    if not director:
        director = User(
            email="onlymoney@gmail.com",
            password="evenmoremoney",
            forename="Scrooge",
            surname="McDuck"
        )
        database.session.add(director)
        database.session.commit()

        userRole = UserRole(
            userId=director.id,
            roleId=directorRole.id
        )
        database.session.add(userRole)
        database.session.commit()