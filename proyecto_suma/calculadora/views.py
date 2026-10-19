import os
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
    # Carpeta donde se guardarán los PDF
    media_path = os.path.join(settings.BASE_DIR, 'media', 'pdfs')
    os.makedirs(media_path, exist_ok=True)

    mensaje = None

    # Procesar subida de archivo PDF
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        if pdf_file.name.endswith('.pdf'):
            fs = FileSystemStorage(location=media_path)
            fs.save(pdf_file.name, pdf_file)
            mensaje = f"Archivo '{pdf_file.name}' subido con éxito."
        else:
            mensaje = "Error: Por favor selecciona únicamente archivos con extensión .pdf."

    # Listar todos los archivos PDF guardados para descarga
    archivos_pdf = []
    if os.path.exists(media_path):
        archivos_pdf = [f for f in os.listdir(media_path) if f.endswith('.pdf')]

    return render(request, 'multimedia.html', {
        'mensaje': mensaje,
        'archivos_pdf': archivos_pdf,
        'MEDIA_URL': '/media/pdfs/'
    })