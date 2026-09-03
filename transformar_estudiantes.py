from pathlib import Path
import csv
import json

# Carpeta raíz de tu proyecto
BASE_DIR = Path(r"C:\Users\salak403\Desktop\Python")

# Rutas completas usando el operador / de pathlib
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"

print("Hola, Aplicaciones y Servicios Web")

def transformar_estudiante(fila: dict) -> dict:
    """Transforma un registro individual de estudiante según los requerimientos."""
    # Concatenar nombre y apellido
    nombre_completo = f"{fila.get('nombre', '')} {fila.get('apellido', '')}".strip()
    
    # Mapear estado booleano a 'Activo' o 'Inactivo'
    activo_str = str(fila.get('activo', '')).strip().lower()
    estado = "Activo" if activo_str in ("true", "1", "yes", "si") else "Inactivo"

    return {
        "id": fila.get("codigo"),
        "nombre_completo": nombre_completo,
        "semestre": int(fila.get("semestre", 0)),
        "promedio": float(fila.get("promedio", 0.0)),
        "estado": estado
        # El campo 'correo' se omite intencionalmente
    }

def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)

def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)

# Flujo principal de ejecución
if __name__ == "__main__":
    # 1 y 2. Leer el archivo CSV y convertir filas
    estudiantes_transformados = []
    
    if RUTA_CSV.exists():
        with open(RUTA_CSV, encoding="utf-8") as archivo_csv:
            lector = csv.DictReader(archivo_csv)
            for fila in lector:
                # 3 y 4. Transformar cada registro
                estudiante_trans = transformar_estudiante(fila)
                estudiantes_transformados.append(estudiante_trans)
        
        # 6. Serializar y guardar el JSON
        serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
        print(f"Archivo JSON generado: {RUTA_JSON}")

        # 7. Deserializar el JSON generado para comprobar
        estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

        print("\nDatos recuperados desde el JSON:")
        if estudiantes_recuperados:
            print(estudiantes_recuperados[0])
        print(f"Total recuperado: {len(estudiantes_recuperados)}")
    else:
        print(f"No se encontró el archivo CSV en la ruta: {RUTA_CSV}. Asegúrate de crearlo dentro de la carpeta 'datos/'.")