class DevelopmentConfig():
    DEBUG = True
    PORT = 8080
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = ''
    
config = {
    'development': DevelopmentConfig
}