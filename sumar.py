import sys
import os

archivo_resultado = "resultado.txt"

# 1. Leer el total acumulado anterior (si existe)
acumulado = 0
if os.path.exists(archivo_resultado):
    with open(archivo_resultado, "r") as f:
        contenido = f.read().strip()
        if contenido.lstrip('-').isdigit():
            acumulado = int(contenido)

# 2. Obtener los números ingresados por parámetro (ej: python sumar.py 15 25 10)
if len(sys.argv) > 1:
    numeros = [int(arg) for arg in sys.argv[1:] if arg.lstrip('-').isdigit()]
else:
    # Si ejecutas el script sin parámetros, sumará 5 por defecto
    numeros = [5]

suma_ingresada = sum(numeros)
nuevo_total = acumulado + suma_ingresada

# 3. Guardar el resultado en el archivo
with open(archivo_resultado, "w") as f:
    f.write(str(nuevo_total))

print("====================================")
print(f"Total acumulado anterior : {acumulado}")
print(f"Números a sumar         : {numeros} (Suma = {suma_ingresada})")
print(f"Nuevo Total acumulado    : {nuevo_total}")
print("====================================")