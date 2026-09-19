from datetime import timedelta;
import os;

databaseUrl = os.environ.get('DATABASE_URL');
jwtSecret = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-change-in-production')
mysqlPassword = os.environ.get('MYSQL_ROOT_PASSWORD', 'root')

class Configuration():
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:{mysqlPassword}@{databaseUrl}/authentication'
    JWT_SECRET_KEY = jwtSecret
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days = 30)