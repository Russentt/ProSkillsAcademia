import os
import psycopg2
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies
from dotenv import load_dotenv
from config import config
from flask_jwt_extended import jwt_required, get_jwt_identity


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
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conexion_db = psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/sign')
def signup():
    return render_template('sign-up.html')

@app.route('/recover')
def password_recover():
    return render_template('password-recover.html')

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
                sql = """
                SELECT id, correo FROM usuarios 
                WHERE (correo = %s OR id::text = %s) AND password = %s;
            """ 
                cursor.execute(sql, (user, user, password))
                usuario_encontrado = cursor.fetchone()
                cursor.close()
                
                # Si el usuario es encontrado se le asigna un token de acceso y se le redirecciona al home
                if usuario_encontrado is not None:
                    token = create_access_token(identity=str(usuario_encontrado[0]))
                    respuesta = redirect(url_for('cuenta'))
                    set_access_cookies(respuesta, token)
                
                    return respuesta
                # Si el usuario no coincide se le redirecciona al login con un mensaje de error
                else:
                    flash("Usuario o contraseña incorrectos")
                    return redirect(url_for('login'))
            except Exception as ex:
               print(f"Error en el servidor: {ex}") 
            flash("Ocurrió un error inesperado en el servidor.")
            return redirect(url_for('login'))

@app.route('/account', methods=["GET"])
@jwt_required()
def cuenta():
    try:
        usuario = get_jwt_identity() 
        
        cursor = conexion_db.cursor()
        sql = """SELECT nombre, apellido, correo, estado, fecha_registro FROM usuarios WHERE id = %s::int;"""
        cursor.execute(sql, (usuario,))
        datos = cursor.fetchone()
        cursor.close()
        
        if not datos:
            flash("usuario no encontrado")
            return redirect(url_for("home"))
            
        encontrado = {
            "nombre": datos[0],
            "apellido": datos[1],
            "correo": datos[2],
            "estado": datos[3],
            "fecha_registro": datos[4].strftime('%d/%m/%Y')
        }   
        
        return render_template('account.html', usuario=encontrado)
        
    except Exception as ex:
        print(f"Error al cargar la cuenta {ex}")
        flash("Error al cargar la informacion")
        return redirect(url_for("home"))
        


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return redirect(url_for('home'))

app.config.from_object(config['development'])
if __name__ == '__main__':
    app.run(host='0.0.0.0', port =app.config['PORT'] , debug=app.config['DEBUG'])