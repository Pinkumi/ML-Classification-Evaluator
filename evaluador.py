"""Calculos manuales de evaluacion, independientes de la interfaz."""


def evaluar_registro(registro, clases):
    _, verdadera, predicha = registro
    resultado = {}
    for clase in clases:
        if verdadera == clase and predicha == clase:
            resultado[clase] = 'TP'
        elif predicha == clase:
            resultado[clase] = 'FP'
        elif verdadera == clase:
            resultado[clase] = 'FN'
        else:
            resultado[clase] = 'TN'
    return resultado


def crear_conteos(clases):
    return {clase: dict.fromkeys(('TP', 'TN', 'FP', 'FN'), 0) for clase in clases}


def acumular(conteos, evaluacion):
    for clase, etiqueta in evaluacion.items():
        conteos[clase][etiqueta] += 1


def dividir(numerador, denominador):
    return numerador / denominador if denominador else 0.0


def calcular_metricas(conteos):
    metricas = {}
    for clase, valores in conteos.items():
        tp, tn, fp, fn = (valores[campo] for campo in ('TP', 'TN', 'FP', 'FN'))
        precision = dividir(tp, tp + fp)
        recall = dividir(tp, tp + fn)
        metricas[clase] = {
            'Precision': precision, 'Recall': recall,
            'Accuracy': dividir(tp + tn, tp + tn + fp + fn),
            'F1': dividir(2 * precision * recall, precision + recall),
        }
    promedios = {nombre: dividir(sum(m[nombre] for m in metricas.values()), len(metricas))
                 for nombre in ('Precision', 'Recall', 'Accuracy', 'F1')}
    return metricas, promedios


class Evaluador:
    """El mismo acumulador permite avanzar un registro o varios por llamada."""

    def __init__(self, registros, clases):
        self.registros = registros
        self.clases = clases
        self.posicion = 0
        self.conteos = crear_conteos(clases)
        self.evaluaciones = []
        self.indices = {clase: indice for indice, clase in enumerate(clases)}
        self.matriz = [[0 for _ in clases] for _ in clases]

    @property
    def terminado(self):
        return self.posicion == len(self.registros)

    def avanzar(self, cantidad=1):
        ultima = None
        for _ in range(min(cantidad, len(self.registros) - self.posicion)):
            registro = self.registros[self.posicion]
            ultima = evaluar_registro(registro, self.clases)
            acumular(self.conteos, ultima)
            self.evaluaciones.append(ultima)
            self.matriz[self.indices[registro[1]]][self.indices[registro[2]]] += 1
            self.posicion += 1
        return ultima

    def resultados(self):
        if not self.terminado:
            raise ValueError("La evaluacion todavia no ha terminado.")
        metricas, promedios = calcular_metricas(self.conteos)
        return self.conteos, metricas, promedios, self.matriz
