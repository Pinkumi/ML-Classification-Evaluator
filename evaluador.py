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
