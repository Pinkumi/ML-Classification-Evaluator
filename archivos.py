"""Lectura y escritura de archivos CSV."""
from pathlib import Path
import csv
import unicodedata


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                   if not unicodedata.combining(c)).strip()


def leer_csv(ruta, numero_clases, encabezado=None):
    """Encabezado None detecta nombres habituales; True acepta cualquier nombre."""
    if not isinstance(numero_clases, int) or numero_clases < 2:
        raise ValueError("La cantidad de clases debe ser un entero mayor o igual a 2.")
    ruta = Path(ruta)
    if ruta.suffix.lower() != '.csv':
        raise ValueError("Seleccione un archivo con extension .csv.")
    registros, clases = [], []
    try:
        with ruta.open(encoding='utf-8-sig', newline='') as archivo:
            lector = csv.reader(archivo, strict=True)
            for indice, fila in enumerate(lector):
                if len(fila) != 3:
                    raise ValueError(f"Fila {lector.line_num}: se requieren exactamente tres columnas.")
                fila = [valor.strip() for valor in fila]
                if not all(fila):
                    raise ValueError(f"Fila {lector.line_num}: hay datos incompletos.")
                habitual = (normalizar(fila[0]) in ('id', 'id-dato', 'identificador')
                            and 'clase' in normalizar(fila[1]))
                if indice == 0 and (encabezado is True or (encabezado is None and habitual)):
                    continue
                registros.append(tuple(fila))
                for clase in fila[1:]:
                    if clase not in clases:
                        clases.append(clase)
    except (UnicodeError, csv.Error) as error:
        raise ValueError(f"Contenido CSV invalido: {error}") from error
    if not registros:
        raise ValueError("El archivo no contiene registros.")
    if len(clases) != numero_clases:
        raise ValueError(f"Se detectaron {len(clases)} clases ({', '.join(clases)}); se indicaron {numero_clases}.")
    return registros, clases
