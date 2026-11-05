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


def validar_nombres(carpeta, nombres):
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        raise ValueError("La carpeta de salida no existe.")
    normalizados = []
    for nombre in nombres:
        if (not nombre.strip() or nombre != nombre.strip()
                or any(c in nombre for c in '/\\<>:"|?*')
                or Path(nombre).name != nombre or not nombre.lower().endswith('.csv')):
            raise ValueError("Use nombres de archivo validos terminados en .csv, sin rutas.")
        normalizados.append(nombre.casefold())
    if len(set(normalizados)) != len(normalizados):
        raise ValueError("Los nombres de salida deben ser distintos.")
    return [carpeta / nombre for nombre in nombres]


def escribir_csv(ruta, filas):
    with Path(ruta).open('w', encoding='utf-8-sig', newline='') as archivo:
        csv.writer(archivo).writerows(filas)


def filas_matriz(evaluador):
    if not evaluador.terminado:
        raise ValueError("Termine el procesamiento antes de guardar.")
    return [['Real / Prediccion', *evaluador.clases]] + [
        [clase, *fila] for clase, fila in zip(evaluador.clases, evaluador.matriz)]


def exportar_resultados(evaluador, carpeta, nombres_clases, nombre_final, nombre_matriz):
    conteos, metricas, promedios, _ = evaluador.resultados()
    nombres = [nombres_clases[clase] for clase in evaluador.clases] + [nombre_final, nombre_matriz]
    rutas = validar_nombres(carpeta, nombres)
    documentos = []
    for clase in evaluador.clases:
        documentos.append([['ID-Dato', 'Evaluacion']] + [
            [registro[0], resultado[clase]] for registro, resultado in
            zip(evaluador.registros, evaluador.evaluaciones)])
    filas = [['Sumatorias por clase'], ['Clase', 'TP', 'TN', 'FP', 'FN']]
    filas += [[clase, *(conteos[clase][c] for c in ('TP', 'TN', 'FP', 'FN'))]
              for clase in evaluador.clases]
    filas += [[], ['Metricas individuales'], ['Clase', 'Precision', 'Recall', 'Accuracy', 'F1']]
    filas += [[clase, *(metricas[clase][c] for c in promedios)] for clase in evaluador.clases]
    filas += [[], ['Promedios macro'], ['Metrica', 'Promedio general']]
    filas += [[nombre, valor] for nombre, valor in promedios.items()]
    documentos.extend([filas, filas_matriz(evaluador)])
    # Preparar todo antes de reemplazar los destinos evita archivos CSV truncados.
    import tempfile
    import os
    temporales = []
    try:
        for filas in documentos:
            with tempfile.NamedTemporaryFile(dir=carpeta, suffix='.tmp', delete=False) as temporal:
                temporales.append(Path(temporal.name))
            escribir_csv(temporales[-1], filas)
        for temporal, ruta in zip(temporales, rutas):
            os.replace(temporal, ruta)
    finally:
        for temporal in temporales:
            temporal.unlink(missing_ok=True)
    return rutas
