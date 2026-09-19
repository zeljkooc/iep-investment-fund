from flask import Flask
from flask_migrate import Migrate
from configuration import Configuration
from models import database
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
migrate = Migrate(application, database)

with application.app_context():
    if not database_exists(database.engine.url):
        create_database(database.engine.url)

if __name__ == "__main__":
    application.run(debug=True)