import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies, unset_jwt_cookies
from dotenv import load_dotenv
from config import config
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_jwt_extended import create_access_token
from datetime import timedelta, datetime
import smtplib
from email.mime.text import MIMEText
from flask import request, redirect, url_for, flash, render_template
from flask_jwt_extended import create_access_token, decode_token

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
            especialidad = request.form.get("especialidad", "")
            biografia = request.form.get("biografia", "")

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
                                   VALUES (%s, %s, %s); """
                cursor.execute(sql_profesor, (new_id, especialidad, biografia))

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
            flash("Error intente de nuevo mas tarde. ")
            return redirect(url_for('signup'))


# Recuperar Contraseña
@app.route('/recover', methods=['GET', 'POST'])
def password_recover():
    
    if request.method == 'GET':
        return render_template('password-recover.html')
    
    if request.method == 'POST':
        usuario = None
        user_id = None
        correo = request.form.get("correo")
        
        if correo:
            correo = correo.strip().lower()
        
        try:
            
            cursor = conexion_db.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE LOWER(correo) = %s;", (correo,))
            usuario = cursor.fetchone()
            cursor.close()
            
        except Exception as db_ex:
            print(f"Error en consulta SQL: {db_ex}")
            flash("Error de conexión con la base de datos.")
            return redirect(url_for('password_recover'))
            
        
        if not usuario:
            print(f"Usuario no encontrado: '{correo}'")
            flash("Correo no encontrado, intente de nuevo más tarde.")
            return redirect(url_for('password_recover'))
            
        user_id = usuario[0]
        
        # generar el token
        try:
            import datetime
            tiempo_tok = datetime.timedelta(minutes=15)
            token_temp = create_access_token(identity=str(user_id), expires_delta=tiempo_tok)
            
            flash("Usuario verificado.")
            return redirect(url_for('change_password', token=token_temp))
            
        except Exception as jwt_ex:
            print(f"Error al crear el Token JWT: {jwt_ex}")
            flash("Intente de nuevo más tarde.")
            return redirect(url_for('password_recover'))
        
        
@app.route('/change-password/<token>', methods=['GET', 'POST']) 
def change_password(token):
    
    try:
        
        datos_token = decode_token(token)
        user_id = datos_token['sub']
        
        if request.method == 'GET':
            # Enviar token al html
            return render_template('change-password.html', token=token)
            
        if request.method == 'POST':
            nueva_password = request.form.get("password")
            
            cursor = conexion_db.cursor()
            sql = "UPDATE usuarios SET password = %s WHERE id = %s::int;"
            cursor.execute(sql, (nueva_password, user_id))
            conexion_db.commit()
            cursor.close()
            
            flash("Contraseña actualizada correctamente.")
            return redirect(url_for('login'))
            
    except Exception as e:
        print(f"ERROR EN VALIDA TOKEN: {e}")
        flash("El token de acceso ha expirado o es inválido.")
        return redirect(url_for('password-recover')) 
        
        
#Perfil profesor
@app.route('/accTeacher', methods=['GET'])
@jwt_required() 
def instructor():
    try:
        profesor_id = get_jwt_identity()
        claims = get_jwt()
        rol_usuario = claims.get("rol") 
        
        if rol_usuario != 'instructor':
            flash("Acceso denegado")
            return redirect(url_for('home'))
        
        cursor = conexion_db.cursor()
        
        cursor.execute("SELECT correo FROM usuarios WHERE id = %s::int;", (profesor_id,))
        usuario_base = cursor.fetchone()
        
        if not usuario_base:
            cursor.close()
            flash("Usuario no encontrado")
            return redirect(url_for('home'))
        
        correo_profesor = usuario_base[0]
        
        sql_perfil = """SELECT nombre_completo, correo, estado, especialidad, biografia 
                        FROM V_INSTRUCTOR WHERE correo = %s;"""
        cursor.execute(sql_perfil, (correo_profesor,)) # <-- Pasamos el parámetro real
        datos_profe = cursor.fetchone()
        
        if not datos_profe:
            cursor.close()
            flash("No se encontraron datos de perfil")
            return redirect(url_for('home'))
        
        profe = {
            "nombre_completo": datos_profe[0],
            "correo":          datos_profe[1],
            "estado":          datos_profe[2],
            "especialidad":    datos_profe[3],
            "biografia":       datos_profe[4]
        }
        
        sql_cursos = """SELECT id_curso, titulo, fecha_inicio, estado 
                        FROM vista_curso WHERE id_instructor = %s::int;"""
        cursor.execute(sql_cursos, (profesor_id,)) # <-- Pasamos el parámetro real (ahora con id_curso)
        curso_base = cursor.fetchall()
        
        cursor.close()
        
        lista_cursos = []
        for fila in curso_base:
            lista_cursos.append({
                "id_curso": fila[0],
                "titulo": fila[1],
                "fecha_inicio": fila[2].strftime('%d/%m/%Y') if fila[2] else 'Sin fecha',
                "estado": fila[3]
            })        
            
        return render_template('acc-instructor.html', profesor=profe, cursos=lista_cursos)
        
    except Exception as ex:
        print(f"--- ERROR REAL EN LA TERMINAL: {ex} ---")
        flash("Ocurrió un error inesperado en el servidor.")
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
                    respuesta = redirect(url_for('cuenta')) 
                    
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

@app.route('/cursos')
def courses():
    return render_template('courses.html')

@app.route('/asignar_notas', methods=['GET', 'POST'])
def asignar_notas():
    if request.method == 'GET':
        return render_template('asignar_notas.html')
    
    if request.method == 'POST':
        try:
            flash("¡Calificaciones guardadas correctamente!", "success")
            return redirect(url_for('asignar_notas'))
            
        except Exception as e:
            print(f"Error al guardar notas: {e}")
            flash("Error al procesar las calificaciones.", "danger")
            return redirect(url_for('asignar_notas'))


@app.route('/curso/<nombre_curso>')
def mostrar_curso(nombre_curso):
    try:
        nombre_limpio = nombre_curso.replace('.html', '')
        
        return render_template(f'{nombre_limpio}.html')
    except Exception as ex:
        print(f"Error al buscar plantilla: {ex}")
        return "Curso no encontrado", 404


@app.route('/aula/<nombre_curso>', methods=['GET'])
@jwt_required()  
def aula_virtual(nombre_curso):
    try:
        alumno_id = get_jwt_identity()
        claims = get_jwt()
        rol_usuario = claims.get("rol")
        
        if rol_usuario != 'estudiante' and rol_usuario != 'instructor':
            flash("Acceso denegado a las aulas virtuales.")
            return redirect(url_for('home'))

        plantillas_validas = {
    'java': 'aula-java.html.html',  
    'marketing': 'aula-marketing.html',
    'diseno': 'aula-diseno.html'
}

        curso_clave = nombre_curso.strip().lower()

        if curso_clave in plantillas_validas:
            return render_template(plantillas_validas[curso_clave])
        else:
            return "Aula virtual no encontrada .", 404

    except Exception as ex:
        print(f"--- ERROR : {ex} ---")
        flash("Ocurrió un error al conectar con el aula virtual.")
        return redirect(url_for('home'))


@app.errorhandler(404)
def pagina_no_encontrada(error):
    print(f"error {error}")
    return redirect(url_for('home'))

app.config.from_object(config['development'])
if __name__ == '__main__':
    app.run(host='0.0.0.0', port =app.config['PORT'] , debug=app.config['DEBUG'])