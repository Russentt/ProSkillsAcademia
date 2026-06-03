import os
import psycopg2
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies
from dotenv import load_dotenv
from config import config


load_dotenv()

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

if not SECRET_KEY or not JWT_SECRET_KEY:
    raise ValueError("CRITICAL ERROR: Security keys are missing from environment variables!")

app.secret_key = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

# Configuración avanzada de cookies protegidas
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
app.config["JWT_COOKIE_CSRF_PROTECT"] = True
app.config["JWT_CSRF_IN_COOKIES"] = True

jwt = JWTManager(app)


# Conexion a BD
DATABASE_URL = os.environ.get('DATABASE_URL') 
conexion_db = psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
        if request.method == 'GET': # Se hace la peticion para mostrar el login
            return render_template('login.html')
        
        if request.method == 'POST':
            try:
                # Captura las respuestas del formulario
                user = request.form.get("user") 
                password = request.form.get("password")
                
                if not user or not password:
                    # Verifica que se añada contraseña y correo a los campos
                    flash("correo y contraseña son requeridos")
                    return redirect(url_for('login'))
                
                # Conexion y consulta a la BD
                cursor = conexion_db.cursor() 
                sql = "SELECT correo FROM USUARIOS WHERE correo = %s AND password = %s" 
                cursor.execute(sql, (user, password))
                usuario_encontrado = cursor.fetchone()
                cursor.close()
                
                # Si el usuario es encontrado se le asigna un token de acceso y se le redirecciona al home
                if usuario_encontrado is not None:
                    token = create_access_token(identity=user)
                    respuesta = redirect(url_for('home'))
                    set_access_cookies(respuesta, token)
                
                    return respuesta
                # Si el usuario no coincide se le redirecciona al login con un mensaje de error
                else:
                    flash("Usuario o contraseña incorrectos")
                    return redirect(url_for('login'))
            except Exception as ex:
               return flash("Servidor Caido"), 500

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return redirect(url_for('home'))

app.config.from_object(config['development'])
if __name__ == '__main__':
    app.run(host='0.0.0.0', port =app.config['PORT'] , debug=app.config['DEBUG'])