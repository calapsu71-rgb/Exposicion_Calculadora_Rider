import os
import psycopg2
import MySQLdb
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

    # --- 2. Formulario multibase de datos ---
    if request.method == 'POST' and 'guardar_db' in request.POST:
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        db_destino = request.POST.get('db_destino')
        
        imagen_file = request.FILES.get('imagen_adjunta')
        documento_file = request.FILES.get('documento_adjunto')

        fs_uploads = FileSystemStorage(location=static_uploads_path)

        # Guardar imagen en static
        img_name = ""
        if imagen_file:
            if fs_uploads.exists(imagen_file.name):
                fs_uploads.delete(imagen_file.name)
            img_name = fs_uploads.save(imagen_file.name, imagen_file)

        # Guardar archivo adjunto en static
        doc_name = ""
        if documento_file:
            if fs_uploads.exists(documento_file.name):
                fs_uploads.delete(documento_file.name)
            doc_name = fs_uploads.save(documento_file.name, documento_file)

        # --- LÓGICA DE INSERCIÓN SEGÚN LA BASE DE DATOS SELECCIONADA ---
        try:
            if db_destino == 'postgres':
                # Ejemplo de conexión a PostgreSQL
                # (Asegúrate de ajustar credenciales o variables de entorno)
                conn = psycopg2.connect(
                    dbname=os.environ.get('PGDATABASE', 'tu_db_postgres'),
                    user=os.environ.get('PGUSER', 'tu_usuario'),
                    password=os.environ.get('PGPASSWORD', 'tu_password'),
                    host=os.environ.get('PGHOST', 'localhost'),
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
                mensaje_db = f"✅ Registro guardado exitosamente en **PostgreSQL**."

            elif db_destino == 'mysql':
                # Ejemplo de conexión a MySQL
                conn = MySQLdb.connect(
                    db=os.environ.get('MYSQL_DATABASE', 'tu_db_mysql'),
                    user=os.environ.get('MYSQL_USER', 'root'),
                    passwd=os.environ.get('MYSQL_PASSWORD', 'tu_password'),
                    host=os.environ.get('MYSQL_HOST', 'localhost'),
                    port=int(os.environ.get('MYSQL_PORT', 3306))
                )
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS registros (
                        id INT AUTO_INCREMENT PRIMARY KEY,
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
                mensaje_db = f"✅ Registro guardado exitosamente en **MySQL**."

            elif db_destino == 'mongodb':
                # Ejemplo de conexión a MongoDB
                mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
                client = MongoClient(mongo_uri)
                db = client['calculadora_db']
                collection = db['registros']
                
                doc = {
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'imagen': img_name,
                    'documento': doc_name
                }
                collection.insert_one(doc)
                client.close()
                mensaje_db = f"✅ Registro guardado exitosamente en **MongoDB**."

        except Exception as e:
            mensaje_db = f"⚠️ Datos procesados, pero ocurrió un error al conectar con {db_destino.upper()}: {str(e)}"

    # Listar PDFs de la subida individual
    archivos_pdf = []
    if os.path.exists(static_pdf_path):
        archivos_pdf = [f for f in os.listdir(static_pdf_path) if f.endswith('.pdf')]

    return render(request, 'multimedia.html', {
        'mensaje': mensaje,
        'mensaje_db': mensaje_db,
        'archivos_pdf': archivos_pdf,
    })