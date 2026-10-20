import os
import psycopg2
import pymysql
from pymongo import MongoClient
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage

TXT_FILE_PATH = os.path.join(settings.BASE_DIR, 'resultado.txt')

def index(request):
    if request.method == 'POST':
        num1_raw = request.POST.get('num1', '0')
        num2_raw = request.POST.get('num2', '0')

        try:
            num1 = int(num1_raw)
            num2 = int(num2_raw)
            suma = num1 + num2
        except ValueError:
            suma = 0

        with open(TXT_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(str(suma))

        return redirect('resultado')

    return render(request, 'index.html')


def resultado(request):
    total = "0"
    if os.path.exists(TXT_FILE_PATH):
        with open(TXT_FILE_PATH, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()
            if contenido:
                total = contenido

    return render(request, 'resultado.html', {'total': total})


def multimedia(request):
    # Carpetas dentro de static
    static_pdf_path = os.path.join(settings.BASE_DIR, 'calculadora', 'static', 'calculadora', 'pdfs')
    static_uploads_path = os.path.join(settings.BASE_DIR, 'calculadora', 'static', 'calculadora', 'uploads')
    
    os.makedirs(static_pdf_path, exist_ok=True)
    os.makedirs(static_uploads_path, exist_ok=True)

    mensaje = None
    mensaje_db = None
    resultado_relacion = None

    registros_postgres = []
    registros_mongo = []
    registros_mysql = []

    # --- 1. Subida individual de PDFs ---
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        if pdf_file.name.endswith('.pdf'):
            fs = FileSystemStorage(location=static_pdf_path)
            if fs.exists(pdf_file.name):
                fs.delete(pdf_file.name)
            fs.save(pdf_file.name, pdf_file)
            mensaje = f"Archivo '{pdf_file.name}' subido con éxito."
        else:
            mensaje = "Error: Por favor selecciona únicamente archivos con extensión .pdf."

    # --- 2. Formulario multibase de datos (Guardar registros) ---
    if request.method == 'POST' and 'guardar_db' in request.POST:
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        db_destino = request.POST.get('db_destino')
        
        imagen_file = request.FILES.get('imagen_adjunta')
        documento_file = request.FILES.get('documento_adjunto')

        fs_uploads = FileSystemStorage(location=static_uploads_path)

        img_name = ""
        if imagen_file:
            if fs_uploads.exists(imagen_file.name):
                fs_uploads.delete(imagen_file.name)
            img_name = fs_uploads.save(imagen_file.name, imagen_file)

        doc_name = ""
        if documento_file:
            if fs_uploads.exists(documento_file.name):
                fs_uploads.delete(documento_file.name)
            doc_name = fs_uploads.save(documento_file.name, documento_file)

        try:
            # MONGODB ATLAS
            if db_destino == 'mongodb':
                mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
                client = MongoClient(mongo_uri)
                db = client['calculadora_db']
                collection = db['registros']
                collection.insert_one({
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'imagen': img_name,
                    'documento': doc_name
                })
                client.close()
                mensaje_db = "✅ ¡Registro guardado exitosamente en MongoDB Atlas!"

            # POSTGRESQL (RENDER)
            elif db_destino == 'postgres':
                conn = psycopg2.connect(
                    dbname=os.environ.get('PGDATABASE', 'calculadora_db_v9jh'),
                    user=os.environ.get('PGUSER', 'camilo'),
                    password=os.environ.get('PGPASSWORD', 'yAPgTZN8PQfkbzHAcCukAeWKEB9lFBAU'),
                    host=os.environ.get('PGHOST', 'dpg-dbb47nifngtc739rvna0-a.oregon-postgres.render.com'),
                    port=os.environ.get('PGPORT', '5432')
                )
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS registros (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(255),
                        descripcion TEXT,
                        imagen VARCHAR(255),
                        documento VARCHAR(255)
                    )
                """)
                cursor.execute("""
                    INSERT INTO registros (nombre, descripcion, imagen, documento)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, descripcion, img_name, doc_name))
                conn.commit()
                cursor.close()
                conn.close()
                mensaje_db = "✅ ¡Registro guardado en PostgreSQL (Render)!"

            # MYSQL (FREESQLDATABASE)
            elif db_destino == 'mysql':
                connection = pymysql.connect(
                    host=os.environ.get('MYSQL_HOST', 'sql10.freesqldatabase.com'),
                    user=os.environ.get('MYSQL_USER', 'sql10839122'),
                    password=os.environ.get('MYSQL_PASSWORD', '1xPkzPTAPF'),
                    database=os.environ.get('MYSQL_DB', 'sql10839122'),
                    port=int(os.environ.get('MYSQL_PORT', 3306))
                )
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS registros_mysql (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            nombre VARCHAR(255),
                            descripcion TEXT,
                            imagen VARCHAR(255),
                            documento VARCHAR(255)
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO registros_mysql (nombre, descripcion, imagen, documento)
                        VALUES (%s, %s, %s, %s)
                    """, (nombre, descripcion, img_name, doc_name))
                    connection.commit()
                connection.close()
                mensaje_db = "✅ ¡Registro guardado en MySQL (FreeSQLDatabase)!"

        except Exception as e:
            mensaje_db = f"⚠️ Error al guardar: {str(e)}"

    # --- 3. Demostración de Relaciones (1:1, 1:N, N:M) ---
    if request.method == 'POST' and 'probar_relacion' in request.POST:
        db_elegida = request.POST.get('db_relaciones')
        tipo_relacion = request.POST.get('tipo_relacion')

        try:
            if db_elegida == 'postgres':
                conn = psycopg2.connect(
                    dbname=os.environ.get('PGDATABASE', 'calculadora_db_v9jh'),
                    user=os.environ.get('PGUSER', 'camilo'),
                    password=os.environ.get('PGPASSWORD', 'yAPgTZN8PQfkbzHAcCukAeWKEB9lFBAU'),
                    host=os.environ.get('PGHOST', 'dpg-dbb47nifngtc739rvna0-a.oregon-postgres.render.com'),
                    port=os.environ.get('PGPORT', '5432')
                )
                cursor = conn.cursor()

                if tipo_relacion == '1:1':
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS estudiantes_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS expedientes_pg (
                            id SERIAL PRIMARY KEY, 
                            estudiante_id INT UNIQUE REFERENCES estudiantes_pg(id) ON DELETE CASCADE,
                            promedio FLOAT
                        );
                        INSERT INTO estudiantes_pg (nombre) VALUES ('Camilo') RETURNING id;
                    """)
                    est_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO expedientes_pg (estudiante_id, promedio) VALUES (%s, 4.5);", (est_id,))
                    conn.commit()
                    resultado_relacion = f"PostgreSQL [1:1]: Estudiante ID {est_id} vinculado con clave foránea UNIQUE a Expediente."

                elif tipo_relacion == '1:N':
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS profesores_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS cursos_pg (
                            id SERIAL PRIMARY KEY, 
                            titulo VARCHAR(100), 
                            profesor_id INT REFERENCES profesores_pg(id)
                        );
                        INSERT INTO profesores_pg (nombre) VALUES ('Prof. García') RETURNING id;
                    """)
                    prof_id = cursor.fetchone()[0]
                    cursor.execute("""
                        INSERT INTO cursos_pg (titulo, profesor_id) VALUES ('Bases de Datos', %s), ('Desarrollo Web', %s);
                    """, (prof_id, prof_id))
                    conn.commit()
                    resultado_relacion = f"PostgreSQL [1:N]: Profesor ID {prof_id} asignado a múltiples cursos."

                elif tipo_relacion == 'N:M':
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS alumnos_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS materias_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS alumno_materia (
                            alumno_id INT REFERENCES alumnos_pg(id),
                            materia_id INT REFERENCES materias_pg(id),
                            PRIMARY KEY (alumno_id, materia_id)
                        );
                        INSERT INTO alumnos_pg (nombre) VALUES ('Ana') RETURNING id;
                    """)
                    alum_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO materias_pg (nombre) VALUES ('Matemáticas') RETURNING id;")
                    mat_id = cursor.fetchone()[0]
                    cursor.execute("INSERT INTO alumno_materia (alumno_id, materia_id) VALUES (%s, %s);", (alum_id, mat_id))
                    conn.commit()
                    resultado_relacion = f"PostgreSQL [N:M]: Creada tabla pivote 'alumno_materia' asociando Alumno {alum_id} con Materia {mat_id}."

                cursor.close()
                conn.close()

            elif db_elegida == 'mysql':
                connection = pymysql.connect(
                    host=os.environ.get('MYSQL_HOST', 'sql10.freesqldatabase.com'),
                    user=os.environ.get('MYSQL_USER', 'sql10839122'),
                    password=os.environ.get('MYSQL_PASSWORD', '1xPkzPTAPF'),
                    database=os.environ.get('MYSQL_DB', 'sql10839122'),
                    port=int(os.environ.get('MYSQL_PORT', 3306))
                )
                with connection.cursor() as cursor:
                    if tipo_relacion == '1:1':
                        cursor.execute("CREATE TABLE IF NOT EXISTS usuarios_ms (id INT AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(100));")
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS perfiles_ms (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                usuario_id INT UNIQUE,
                                bio TEXT,
                                FOREIGN KEY (usuario_id) REFERENCES usuarios_ms(id)
                            );
                        """)
                        cursor.execute("INSERT INTO usuarios_ms (nombre) VALUES ('Carlos');")
                        u_id = cursor.lastrowid
                        cursor.execute("INSERT INTO perfiles_ms (usuario_id, bio) VALUES (%s, 'Perfil de programador');", (u_id,))
                        connection.commit()
                        resultado_relacion = f"MySQL [1:1]: Usuario ID {u_id} creado con restricción UNIQUE en perfil."

                    elif tipo_relacion == '1:N':
                        cursor.execute("CREATE TABLE IF NOT EXISTS categorias_ms (id INT AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(100));")
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS productos_ms (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                nombre VARCHAR(100),
                                categoria_id INT,
                                FOREIGN KEY (categoria_id) REFERENCES categorias_ms(id)
                            );
                        """)
                        cursor.execute("INSERT INTO categorias_ms (nombre) VALUES ('Tecnología');")
                        cat_id = cursor.lastrowid
                        cursor.execute("INSERT INTO productos_ms (nombre, categoria_id) VALUES ('Laptop', %s), ('Mouse', %s);", (cat_id, cat_id))
                        connection.commit()
                        resultado_relacion = f"MySQL [1:N]: Categoría 'Tecnología' (ID {cat_id}) vinculada a varios productos."

                    elif tipo_relacion == 'N:M':
                        cursor.execute("CREATE TABLE IF NOT EXISTS autores_ms (id INT AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(100));")
                        cursor.execute("CREATE TABLE IF NOT EXISTS libros_ms (id INT AUTO_INCREMENT PRIMARY KEY, titulo VARCHAR(100));")
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS autor_libro (
                                autor_id INT,
                                libro_id INT,
                                PRIMARY KEY (autor_id, libro_id),
                                FOREIGN KEY (autor_id) REFERENCES autores_ms(id),
                                FOREIGN KEY (libro_id) REFERENCES libros_ms(id)
                            );
                        """)
                        cursor.execute("INSERT INTO autores_ms (nombre) VALUES ('Gabriel García Márquez');")
                        aut_id = cursor.lastrowid
                        cursor.execute("INSERT INTO libros_ms (titulo) VALUES ('Cien Años de Soledad');")
                        lib_id = cursor.lastrowid
                        cursor.execute("INSERT INTO autor_libro (autor_id, libro_id) VALUES (%s, %s);", (aut_id, lib_id))
                        connection.commit()
                        resultado_relacion = f"MySQL [N:M]: Relación N:M creada en tabla pivote 'autor_libro'."

                connection.close()

            elif db_elegida == 'mongodb':
                mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
                client = MongoClient(mongo_uri)
                db = client['calculadora_db']

                if tipo_relacion == '1:1':
                    doc = {
                        'nombre': 'Elena',
                        'expediente': {'promedio': 4.8, 'estado': 'Activo'}
                    }
                    res = db['relacion_1a1'].insert_one(doc)
                    resultado_relacion = f"MongoDB Atlas [1:1]: Documento embebido creado con ID {res.inserted_id}."

                elif tipo_relacion == '1:N':
                    doc = {
                        'profesor': 'Prof. Martínez',
                        'cursos': [{'codigo': 'BD101', 'nombre': 'Bases de Datos'}, {'codigo': 'WEB201', 'nombre': 'Frontend Django'}]
                    }
                    res = db['relacion_1aN'].insert_one(doc)
                    resultado_relacion = f"MongoDB Atlas [1:N]: Documento creado con Array de cursos embebidos."

                elif tipo_relacion == 'N:M':
                    res = db['relacion_NmM'].insert_one({
                        'estudiante': 'Lucía',
                        'cursos_ids': ['CURSO_PG_1', 'CURSO_PG_2']
                    })
                    resultado_relacion = f"MongoDB Atlas [N:M]: Referenciación NoSQL mediante array de identificadores."

                client.close()

        except Exception as e:
            resultado_relacion = f"⚠️ Error en relaciones: {str(e)}"

    # --- 4. Consultar registros para mostrarlos en tablas ---
    # PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('PGDATABASE', 'calculadora_db_v9jh'),
            user=os.environ.get('PGUSER', 'camilo'),
            password=os.environ.get('PGPASSWORD', 'yAPgTZN8PQfkbzHAcCukAeWKEB9lFBAU'),
            host=os.environ.get('PGHOST', 'dpg-dbb47nifngtc739rvna0-a.oregon-postgres.render.com'),
            port=os.environ.get('PGPORT', '5432')
        )
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS registros (id SERIAL PRIMARY KEY, nombre VARCHAR(255), descripcion TEXT, imagen VARCHAR(255), documento VARCHAR(255));")
        cursor.execute("SELECT id, nombre, descripcion, imagen, documento FROM registros ORDER BY id DESC LIMIT 5;")
        registros_postgres = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception:
        pass

    # MySQL
    try:
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'sql10.freesqldatabase.com'),
            user=os.environ.get('MYSQL_USER', 'sql10839122'),
            password=os.environ.get('MYSQL_PASSWORD', '1xPkzPTAPF'),
            database=os.environ.get('MYSQL_DB', 'sql10839122'),
            port=int(os.environ.get('MYSQL_PORT', 3306))
        )
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS registros_mysql (id INT AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(255), descripcion TEXT, imagen VARCHAR(255), documento VARCHAR(255));")
            cursor.execute("SELECT id, nombre, descripcion, imagen, documento FROM registros_mysql ORDER BY id DESC LIMIT 5;")
            registros_mysql = cursor.fetchall()
        connection.close()
    except Exception:
        pass

    # MongoDB
    try:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        db = client['calculadora_db']
        registros_mongo = list(db['registros'].find().sort('_id', -1).limit(5))
        client.close()
    except Exception:
        pass

    # Listar PDFs de la subida individual
    archivos_pdf = []
    if os.path.exists(static_pdf_path):
        archivos_pdf = [f for f in os.listdir(static_pdf_path) if f.endswith('.pdf')]

    return render(request, 'multimedia.html', {
        'mensaje': mensaje,
        'mensaje_db': mensaje_db,
        'resultado_relacion': resultado_relacion,
        'archivos_pdf': archivos_pdf,
        'registros_postgres': registros_postgres,
        'registros_mysql': registros_mysql,
        'registros_mongo': registros_mongo,
    })