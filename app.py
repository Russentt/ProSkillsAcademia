from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import JWTManager, create_access_token,set_access_cookies
from config import config
import psycopg2
import os
from dotenv import load_dotenv # Libreria que busca y lee archivos ocultos
load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") # Clave que se envia a flash para mostrar los mensajes(Usuario y contraseña incorrectos)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")  #Contraseña que encripta los tokens
app.config["JWT_TOKEN_LOCATION"] = ["cookies"] # Guarda los token de forma automatica en el navegador 
jwt = JWTManager(app) # Activa el uso de admimistracion de los token

# Conexion a BD
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conexion_db = psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    return render_template('index.html')

@app.rout('/account')
def account():
    return render_template('account.html')

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
               return jsonify({"mensaje": "Error en el servidor"}), 500

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return redirect(url_for('home'))

app.config.from_object(config['development'])
if __name__ == '__main__':
    app.run(host='0.0.0.0', port =app.config['PORT'] , debug=app.config['DEBUG'])