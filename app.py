import os
import psycopg2
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies, unset_jwt_cookies
from dotenv import load_dotenv
from config import config
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_jwt_extended import create_access_token
from datetime import timedelta, datetime
 
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
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
jwt = JWTManager(app)

# Si no tiene token los redirige al login
@jwt.unauthorized_loader
def sin_token(error_string):
    flash("Debes iniciar sesion para acceder")
    return redirect(url_for('login'))

# Redirige al login cuando el token expire
@jwt.expired_token_loader
def token_expirado_callback(jwt_header, jwt_payload):
    flash("Tu sesión ha expirado por inactividad. Por favor, vuelve a ingresar.")
    return redirect(url_for('login'))

# Conexion a BD
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conexion_db = psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/sign', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('sign-up.html')
    
    if request.method == 'POST':
        try:
            nombre_apellido = request.form.get("nombre_apellido")
            correo = request.form.get("correo")
            rol = request.form.get("rol")
            password = request.form.get("password")
            re_password = request.form.get("re_password")

            if not nombre_apellido or not correo or not password or not rol:
                flash("todos los campos son obligatorios")
                return redirect(url_for('signup'))
            
            if re_password != password and password != re_password:
                flash("La contraseña debe ser igual en los 2 campos")
                return redirect(url_for('signup'))    
           
            partes = nombre_apellido.strip().split(" ", 1)
            nombre = partes[0]
            apellido = partes[1] if len(partes) > 1 else ""
            cursor = conexion_db.cursor()

            sql_usuario = """ INSERT INTO usuarios (nombre, apellido, correo, password, estado)
                              VALUES (%s, %s, %s, %s, 'Activo') RETURNING id; """

            cursor.execute(sql_usuario, (nombre, apellido, correo, password))
            new_id = cursor.fetchone()[0]

            if rol == 'estudiante':
                fecha_actual = datetime.now().date()
                id_pago_defecto = 1

                sql_estudiante = """ INSERT INTO estudiante (id_estudiante, fecha_ingreso, id_pago)
                                     VALUES (%s, %s, %s); """
                cursor.execute(sql_estudiante, (new_id, fecha_actual, id_pago_defecto))

            elif rol == 'instructor':

                sql_profesor = """ INSERT INTO instructor (id_instructor ,especialidad, biografia)
                                   VALUES (%s, 'Profesor', 'Hacealgo'); """
                cursor.execute(sql_profesor, (new_id,))

            elif rol == 'administrador':
                sql_admin = """ INSERT INTO administrador (id_administrador,nivel_acceso)
                                VALUES (%s ,'Completo'); """
                cursor.execute(sql_admin, (new_id,))

            else:
                flash("Debe escojer un ROL!")
                return redirect(url_for('signup'))
            
            conexion_db.commit()
            cursor.close()
            flash("Cuenta creada correctamente")
            return redirect(url_for('login'))

        except Exception as ex:
            conexion_db.rollback()
            print(f"Detalle técnico: {ex}\n") 
            flash("Error intente de nuevo mas tarde {ex}")
            return redirect(url_for('signup'))


@app.route('/recover')
def password_recover():
    return render_template('password-recover.html')

#Perfil profesor
@app.route('/accTeacher', methods=['GET'])
@jwt_required()
def instructor():
    try:
        # Token profesor
        profesor_id = get_jwt_identity()
        claims = get_jwt()
        rol_usuario = claims.get("rol") 
        
        # Si el rol no es instructor lo redirige al home
        if rol_usuario != 'instructor':
            flash("Acceso denegado")
            return redirect(url_for('home'))
        
        # Conexion BD
        cursor = conexion_db.cursor()
        cursor.execute("SELECT correo FROM usuarios WHERE id = %s::int;", (profesor_id,)) # Traer correo de usuario
        usuario_base = cursor.fetchone()
        
        # Si el usuario no se encuentra redireccion al home
        if not usuario_base:
            cursor.close()
            flash("usuario no encontrado")
            return redirect(url_for('home'))
        
        # valor del correo -> (posicion del correo )
        correo_profesor = usuario_base[0]
        
        # Consulta a la vista
        sql = """SELECT nombre_completo, correo, estado, especialidad, biografia FROM V_INSTRUCTOR WHERE correo = %s;"""
        
        # Executar la consulta donde el correo ingresado sea igual al del instructor
        cursor.execute(sql, (correo_profesor,))
        datos_profe = cursor.fetchone()
        cursor.close()
        
        # Si no se encuentra los datos redireccion al home
        if not datos_profe:
            flash("No se encontraron datos")
            return redirect(url_for('home'))
        
        # Asignar posicion de los datos del instructor
        profe = {
            "nombre_completo": datos_profe[0],
            "correo":          datos_profe[1],
            "estado":          datos_profe[2],
            "especialidad":    datos_profe[3],
            "biografia":       datos_profe[4]
        }
        
        # Redireccion al html de la cuenta de instructor 
        return render_template('acc-instructor.html', profesor = profe)
        
    except Exception as ex:
        print(f"Error al cargar {ex}")
        flash("Intente de nuevo mas tarde")
        return redirect(url_for('login'))   
    

@app.route('/skills')
def programas():
    return render_template('skills.html')

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
                # Execucion de la consulta 
                cursor.execute(sql, (user, user, password))
                usuario_encontrado = cursor.fetchone()
                
                # Si no se encuentra el usuario retorna al login
                if usuario_encontrado is None:
                    cursor.close
                    flash("Usuario o Contraseña incorrectos")
                    return redirect(url_for('login'))
                
                # valor del id 
                user_id = usuario_encontrado[0]
                rol = None # Asignar un rol por defecto
                
                # Rol admin            
                cursor.execute("SELECT id_administrador from administrador WHERE id_administrador = %s::int;", (user_id,))  
                if cursor.fetchone() is not None:
                    rol = 'admin'
                    
                else: # Rol instructor
                    cursor.execute("SELECT id_instructor from instructor WHERE id_instructor = %s::int;", (user_id,))              
                    if cursor.fetchone() is not None:
                        rol = 'instructor'
                    
                    else: # Rol estudiante
                        cursor.execute("SELECT id_estudiante from estudiante WHERE id_estudiante = %s::int;", (user_id,))
                        if cursor.fetchone() is not None:
                            rol = 'estudiante'

                cursor.close()
                
                if rol is None:
                    flash("Tu cuenta no tiene un rol asignado en el sistema.")
                    return redirect(url_for('login'))    
                
                # Asignar rol para despues asignarlo al token
                rol_token = {
                "rol": rol
                } 
                
                # Token con el rol asignado
                token = create_access_token(identity=str(user_id), additional_claims=rol_token)
                
                # Redireccion dependiendo del rol
                if rol == 'administrador':
                    respuesta = redirect(url_for('cuenta')) # Ignacio haz la cuenta del admin pronto, agarra la pala
                    
                elif rol == 'instructor':
                    respuesta = redirect(url_for('instructor'))
                
                else:
                    respuesta = redirect(url_for('cuenta'))

                # Guardar el token 
                set_access_cookies(respuesta, token)                
                return respuesta
                
            except Exception as ex:
                print(f"Error en el servidor: {ex}") 
                flash("Ocurrió un error inesperado en el servidor.")
                return redirect(url_for('login'))

@app.route('/account', methods=["GET"])
@jwt_required()
def cuenta():
    try:
        usuario = get_jwt_identity() 
        claims = get_jwt()
        rol_usuario = claims.get("rol")
        
        if rol_usuario == 'instructor':
            return redirect(url_for('instructor'))

        
        cursor = conexion_db.cursor()
        sql = """SELECT nombre, apellido, correo, estado, fecha_registro FROM usuarios WHERE id = %s::int;"""
        cursor.execute(sql, (usuario,))
        datos = cursor.fetchone()
        
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
        
@app.route('/logout', methods=['GET'])
def logout():
    respuesta = redirect(url_for('login'))
    unset_jwt_cookies(respuesta)
    flash("Sesión cerrada correctamente.")
    return respuesta

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return redirect(url_for('home'))

app.config.from_object(config['development'])
if __name__ == '__main__':
    app.run(host='0.0.0.0', port =app.config['PORT'] , debug=app.config['DEBUG'])