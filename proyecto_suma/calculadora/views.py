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

    # --- 3. Demostración de Relaciones (1:1, 1:N, N:M) con Múltiples Registros ---
    if request.method == 'POST' and 'probar_relacion' in request.POST:
        db_elegida = request.POST.get('db_relaciones')
        tipo_relacion = request.POST.get('tipo_relacion')

        try:
            # POSTGRESQL (Render)
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
                    """)
                    estudiantes = ['Camilo Cuaran', 'Ana Martínez', 'Jhamilton Silva']
                    promedios = [4.5, 4.8, 4.2]
                    ids_creados = []
                    for nom, prom in zip(estudiantes, promedios):
                        cursor.execute("INSERT INTO estudiantes_pg (nombre) VALUES (%s) RETURNING id;", (nom,))
                        e_id = cursor.fetchone()[0]
                        cursor.execute("INSERT INTO expedientes_pg (estudiante_id, promedio) VALUES (%s, %s);", (e_id, prom))
                        ids_creados.append(str(e_id))
                    conn.commit()
                    resultado_relacion = f"PostgreSQL [1:1]: Insertados 3 estudiantes (IDs: {', '.join(ids_creados)}) con expedientes 1:1 únicos."

                elif tipo_relacion == '1:N':
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS profesores_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS cursos_pg (
                            id SERIAL PRIMARY KEY, 
                            titulo VARCHAR(100), 
                            profesor_id INT REFERENCES profesores_pg(id)
                        );
                    """)
                    cursor.execute("INSERT INTO profesores_pg (nombre) VALUES ('Prof. García') RETURNING id;")
                    prof_id = cursor.fetchone()[0]
                    cursos = ['Bases de Datos I', 'Desarrollo Web Django', 'Arquitectura en la Nube']
                    for curso in cursos:
                        cursor.execute("INSERT INTO cursos_pg (titulo, profesor_id) VALUES (%s, %s);", (curso, prof_id))
                    conn.commit()
                    resultado_relacion = f"PostgreSQL [1:N]: Profesor ID {prof_id} asignado a {len(cursos)} cursos."

                elif tipo_relacion == 'N:M':
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS alumnos_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS materias_pg (id SERIAL PRIMARY KEY, nombre VARCHAR(100));
                        CREATE TABLE IF NOT EXISTS alumno_materia (
                            alumno_id INT REFERENCES alumnos_pg(id),
                            materia_id INT REFERENCES materias_pg(id),
                            PRIMARY KEY (alumno_id, materia_id)
                        );
                    """)
                    cursor.execute("INSERT INTO alumnos_pg (nombre) VALUES ('Camilo'), ('Laura') RETURNING id;")
                    alumnos_ids = [r[0] for r in cursor.fetchall()]
                    cursor.execute("INSERT INTO materias_pg (nombre) VALUES ('Matemáticas'), ('Programación') RETURNING id;")
                    materias_ids = [r[0] for r in cursor.fetchall()]
                    for a_id in alumnos_ids:
                        for m_id in materias_ids:
                            cursor.execute("INSERT INTO alumno_materia (alumno_id, materia_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (a_id, m_id))
                    conn.commit()
                    resultado_relacion = f"PostgreSQL [N:M]: Múltiples relaciones creadas en la tabla pivote 'alumno_materia'."

                cursor.close()
                conn.close()

            # MYSQL (FreeSQLDatabase)
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
                        usuarios = ['Carlos Perez', 'Sofia Gomez', 'Mateo Rios']
                        u_ids = []
                        for u in usuarios:
                            cursor.execute("INSERT INTO usuarios_ms (nombre) VALUES (%s);", (u,))
                            u_id = cursor.lastrowid
                            cursor.execute("INSERT INTO perfiles_ms (usuario_id, bio) VALUES (%s, %s);", (u_id, f"Perfil de {u}"))
                            u_ids.append(str(u_id))
                        connection.commit()
                        resultado_relacion = f"MySQL [1:1]: Creados 3 usuarios (IDs: {', '.join(u_ids)}) con perfiles 1:1."

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
                        productos = ['Laptop Asus', 'Mouse Logi', 'Teclado Mecánico']
                        for p in productos:
                            cursor.execute("INSERT INTO productos_ms (nombre, categoria_id) VALUES (%s, %s);", (p, cat_id))
                        connection.commit()
                        resultado_relacion = f"MySQL [1:N]: Categoría 'Tecnología' (ID {cat_id}) vinculada a {len(productos)} productos."

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
                        cursor.execute("INSERT INTO autores_ms (nombre) VALUES ('Gabo'), ('Mario Vargas Llosa');")
                        cursor.execute("INSERT INTO libros_ms (titulo) VALUES ('Cien Años de Soledad'), ('La Ciudad y los Perros');")
                        connection.commit()
                        resultado_relacion = f"MySQL [N:M]: Múltiples autores y libros en tabla intermedia 'autor_libro'."

                connection.close()

            # MONGODB ATLAS (NoSQL)
            elif db_elegida == 'mongodb':
                mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
                client = MongoClient(mongo_uri)
                db = client['calculadora_db']

                if tipo_relacion == '1:1':
                    docs = [
                        {'nombre': 'Elena', 'expediente': {'promedio': 4.8, 'estado': 'Activo'}},
                        {'nombre': 'Camilo', 'expediente': {'promedio': 4.5, 'estado': 'Activo'}},
                        {'nombre': 'Julian', 'expediente': {'promedio': 4.1, 'estado': 'Graduado'}}
                    ]
                    res = db['relacion_1a1'].insert_many(docs)
                    resultado_relacion = f"MongoDB Atlas [1:1]: Insertados {len(res.inserted_ids)} documentos embebidos."

                elif tipo_relacion == '1:N':
                    doc = {
                        'profesor': 'Prof. Martínez',
                        'cursos': [
                            {'codigo': 'BD101', 'nombre': 'Bases de Datos'},
                            {'codigo': 'WEB201', 'nombre': 'Frontend Django'},
                            {'codigo': 'NOSQL301', 'nombre': 'Modelado MongoDB'}
                        ]
                    }
                    res = db['relacion_1aN'].insert_one(doc)
                    resultado_relacion = f"MongoDB Atlas [1:N]: Documento creado con un Array de 3 cursos embebidos."

                elif tipo_relacion == 'N:M':
                    docs = [
                        {'estudiante': 'Lucía', 'cursos_ids': ['CURSO_PG_1', 'CURSO_PG_2']},
                        {'estudiante': 'Camilo', 'cursos_ids': ['CURSO_PG_1', 'CURSO_MONGO_1']}
                    ]
                    res = db['relacion_NmM'].insert_many(docs)
                    resultado_relacion = f"MongoDB Atlas [N:M]: {len(res.inserted_ids)} estudiantes con arreglos de referencias."

                client.close()

        except Exception as e:
            resultado_relacion = f"⚠️ Error en relaciones: {str(e)}"

    # --- 4. Consultas generales para tablas ---
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

    try:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        db = client['calculadora_db']
        registros_mongo = list(db['registros'].find().sort('_id', -1).limit(5))
        client.close()
    except Exception:
        pass

    # --- 5. Consultas en vivo de las relaciones para la vista ---
    rel_pg_1a1, rel_pg_1aN, rel_pg_NmM = [], [], []
    rel_ms_1a1, rel_ms_1aN, rel_ms_NmM = [], [], []
    rel_mg_1a1, rel_mg_1aN, rel_mg_NmM = [], [], []

    # PostgreSQL Relaciones
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('PGDATABASE', 'calculadora_db_v9jh'),
            user=os.environ.get('PGUSER', 'camilo'),
            password=os.environ.get('PGPASSWORD', 'yAPgTZN8PQfkbzHAcCukAeWKEB9lFBAU'),
            host=os.environ.get('PGHOST', 'dpg-dbb47nifngtc739rvna0-a.oregon-postgres.render.com'),
            port=os.environ.get('PGPORT', '5432')
        )
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT e.nombre, ex.estudiante_id, ex.promedio FROM expedientes_pg ex JOIN estudiantes_pg e ON ex.estudiante_id = e.id ORDER BY ex.id DESC LIMIT 5;")
            rel_pg_1a1 = cursor.fetchall()
        except Exception: pass
        
        try:
            cursor.execute("SELECT p.nombre, c.titulo FROM cursos_pg c JOIN profesores_pg p ON c.profesor_id = p.id ORDER BY c.id DESC LIMIT 5;")
            rel_pg_1aN = cursor.fetchall()
        except Exception: pass

        try:
            cursor.execute("SELECT a.nombre, m.nombre FROM alumno_materia am JOIN alumnos_pg a ON am.alumno_id = a.id JOIN materias_pg m ON am.materia_id = m.id LIMIT 5;")
            rel_pg_NmM = cursor.fetchall()
        except Exception: pass
        cursor.close()
        conn.close()
    except Exception: pass

    # MySQL Relaciones
    try:
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', 'sql10.freesqldatabase.com'),
            user=os.environ.get('MYSQL_USER', 'sql10839122'),
            password=os.environ.get('MYSQL_PASSWORD', '1xPkzPTAPF'),
            database=os.environ.get('MYSQL_DB', 'sql10839122'),
            port=int(os.environ.get('MYSQL_PORT', 3306))
        )
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT u.nombre, p.bio FROM perfiles_ms p JOIN usuarios_ms u ON p.usuario_id = u.id ORDER BY p.id DESC LIMIT 5;")
                rel_ms_1a1 = cursor.fetchall()
            except Exception: pass

            try:
                cursor.execute("SELECT c.nombre, p.nombre FROM productos_ms p JOIN categorias_ms c ON p.categoria_id = c.id ORDER BY p.id DESC LIMIT 5;")
                rel_ms_1aN = cursor.fetchall()
            except Exception: pass

            try:
                cursor.execute("SELECT a.nombre, l.titulo FROM autor_libro al JOIN autores_ms a ON al.autor_id = a.id JOIN libros_ms l ON al.libro_id = l.id LIMIT 5;")
                rel_ms_NmM = cursor.fetchall()
            except Exception: pass
        connection.close()
    except Exception: pass

    # MongoDB Atlas Relaciones
    try:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        db = client['calculadora_db']
        try: rel_mg_1a1 = list(db['relacion_1a1'].find().sort('_id', -1).limit(5))
        except Exception: pass
        try: rel_mg_1aN = list(db['relacion_1aN'].find().sort('_id', -1).limit(5))
        except Exception: pass
        try: rel_mg_NmM = list(db['relacion_NmM'].find().sort('_id', -1).limit(5))
        except Exception: pass
        client.close()
    except Exception: pass

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
        'rel_pg_1a1': rel_pg_1a1, 'rel_pg_1aN': rel_pg_1aN, 'rel_pg_NmM': rel_pg_NmM,
        'rel_ms_1a1': rel_ms_1a1, 'rel_ms_1aN': rel_ms_1aN, 'rel_ms_NmM': rel_ms_NmM,
        'rel_mg_1a1': rel_mg_1a1, 'rel_mg_1aN': rel_mg_1aN, 'rel_mg_NmM': rel_mg_NmM,
    })