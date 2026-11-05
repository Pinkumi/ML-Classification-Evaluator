"""Pruebas sin dependencias externas y sin abrir ventanas."""
import csv
from pathlib import Path
import tempfile
import unittest
from archivos import leer_csv, exportar_resultados, validar_nombres
from evaluador import Evaluador, evaluar_registro, calcular_metricas

RAIZ = Path(__file__).resolve().parents[1]


class PruebasEvaluador(unittest.TestCase):
    def evaluar(self, registros, clases, lote=1000):
        evaluador = Evaluador(registros, clases)
        while not evaluador.terminado:
            evaluador.avanzar(lote)
        return evaluador

    def ejemplo(self):
        return leer_csv(RAIZ / 'datos/ejemplo_clase.csv', 3)

    def test_cuatro_etiquetas(self):
        clases = ['A', 'B', 'C']
        self.assertEqual(evaluar_registro(('1', 'A', 'B'), clases),
                         {'A': 'FN', 'B': 'FP', 'C': 'TN'})
        self.assertEqual(evaluar_registro(('2', 'A', 'A'), clases),
                         {'A': 'TP', 'B': 'TN', 'C': 'TN'})

    def test_ejercicio_profesor(self):
        evaluador = self.evaluar(*self.ejemplo())
        esperado = {'A': {'TP': 3, 'TN': 6, 'FP': 4, 'FN': 2},
                    'B': {'TP': 4, 'TN': 8, 'FP': 2, 'FN': 1},
                    'C': {'TP': 0, 'TN': 8, 'FP': 2, 'FN': 5}}
        self.assertEqual(evaluador.conteos, esperado)
        for conteos in evaluador.conteos.values():
            self.assertEqual(sum(conteos.values()), 15)

    def test_matriz(self):
        evaluador = self.evaluar(*self.ejemplo())
        self.assertEqual(evaluador.matriz, [[3, 1, 1], [0, 4, 1], [4, 1, 0]])
        self.assertEqual(sum(map(sum, evaluador.matriz)), 15)

    def test_metricas_y_macro(self):
        evaluador = self.evaluar(*self.ejemplo())
        _, metricas, promedios, _ = evaluador.resultados()
        esperado = {'A': (3/7, 3/5, 9/15, 1/2),
                    'B': (4/6, 4/5, 12/15, 8/11),
                    'C': (0, 0, 8/15, 0)}
        for clase, valores in esperado.items():
            for nombre, valor in zip(promedios, valores):
                self.assertAlmostEqual(metricas[clase][nombre], valor)
        for indice, nombre in enumerate(promedios):
            self.assertAlmostEqual(promedios[nombre], sum(v[indice] for v in esperado.values()) / 3)

    def test_dos_clases(self):
        evaluador = self.evaluar(*leer_csv(RAIZ / 'datos/ejemplo_adicional.csv', 2))
        self.assertEqual(evaluador.matriz, [[2, 1], [1, 2]])
        for conteos in evaluador.conteos.values():
            self.assertEqual(conteos, {'TP': 2, 'TN': 2, 'FP': 1, 'FN': 1})

    def test_mas_de_tres_clases(self):
        clases = ['A', 'B', 'C', 'D', 'E']
        registros = [(str(i), c, clases[(i+1) % 5]) for i, c in enumerate(clases)]
        evaluador = self.evaluar(registros, clases)
        self.assertEqual(len(evaluador.matriz), 5)
        self.assertEqual(sum(map(sum, evaluador.matriz)), 5)
        for c in clases:
            self.assertEqual(evaluador.conteos[c], {'TP': 0, 'TN': 3, 'FP': 1, 'FN': 1})

    def test_todas_correctas(self):
        evaluador = self.evaluar([('1', 'A', 'A'), ('2', 'B', 'B')], ['A', 'B'])
        _, metricas, promedios, _ = evaluador.resultados()
        self.assertTrue(all(v == 1 for m in metricas.values() for v in m.values()))
        self.assertTrue(all(v == 1 for v in promedios.values()))

    def test_todas_incorrectas(self):
        evaluador = self.evaluar([('1', 'A', 'B'), ('2', 'B', 'A')], ['A', 'B'])
        self.assertTrue(all(v == 0 for v in evaluador.resultados()[2].values()))

    def test_denominadores_cero(self):
        metricas, _ = calcular_metricas({'A': dict.fromkeys(('TP', 'TN', 'FP', 'FN'), 0)})
        self.assertEqual(metricas['A'], dict.fromkeys(('Precision', 'Recall', 'Accuracy', 'F1'), 0))
        evaluador = self.evaluar([('1', 'A', 'B')], ['A', 'B'])
        self.assertEqual(evaluador.resultados()[1]['A']['Precision'], 0)
        self.assertEqual(evaluador.resultados()[1]['B']['Recall'], 0)

    def test_modos_identicos_y_un_paso(self):
        registros, clases = self.ejemplo()
        pasos = Evaluador(registros, clases)
        for indice in range(15):
            pasos.avanzar()
            self.assertEqual(pasos.posicion, indice + 1)
        completo = self.evaluar(registros, clases)
        self.assertEqual(pasos.resultados(), completo.resultados())
        self.assertEqual(pasos.evaluaciones, completo.evaluaciones)

    def test_no_resultados_parciales(self):
        evaluador = Evaluador(*self.ejemplo())
        evaluador.avanzar()
        with self.assertRaises(ValueError):
            evaluador.resultados()
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaises(ValueError):
                exportar_resultados(evaluador, carpeta, {'A': 'A.csv', 'B': 'B.csv', 'C': 'C.csv'},
                                    'final.csv', 'matriz.csv')
            self.assertEqual(list(Path(carpeta).iterdir()), [])

    def test_exportacion(self):
        evaluador = self.evaluar(*self.ejemplo())
        with tempfile.TemporaryDirectory() as carpeta:
            nombres = {c: f'evaluacion_{c}.csv' for c in evaluador.clases}
            rutas = exportar_resultados(evaluador, carpeta, nombres, 'final.csv', 'matriz.csv')
            self.assertEqual(len(rutas), 5)
            self.assertEqual(len(list(Path(carpeta).glob('evaluacion_*.csv'))), 3)
            for clase in evaluador.clases:
                with (Path(carpeta) / nombres[clase]).open(encoding='utf-8-sig', newline='') as archivo:
                    filas = list(csv.reader(archivo))
                self.assertEqual(filas[0], ['ID-Dato', 'Evaluacion'])
                self.assertEqual(filas[1:], [[r[0], e[clase]] for r, e in
                                           zip(evaluador.registros, evaluador.evaluaciones)])
            with rutas[-1].open(encoding='utf-8-sig', newline='') as archivo:
                matriz = list(csv.reader(archivo))
            self.assertEqual(matriz[0], ['Real / Prediccion', 'A', 'B', 'C'])
            self.assertEqual(matriz[1], ['A', '3', '1', '1'])
            with rutas[-2].open(encoding='utf-8-sig', newline='') as archivo:
                filas = list(csv.reader(archivo))
            self.assertIn(['A', '3', '6', '4', '2'], filas)
            self.assertIn(['Promedios macro'], filas)
            self.assertFalse(list(Path(carpeta).glob('*.tmp')))


class PruebasArchivos(unittest.TestCase):
    def leer_texto(self, texto, cantidad=2, encabezado=None):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'datos.csv'
            ruta.write_text(texto, encoding='utf-8-sig')
            return leer_csv(ruta, cantidad, encabezado)

    def test_invalidos(self):
        for texto in ['', 'ID-Dato,Clase verdadera,Clase Prediccion\n', '\n', '1,A\n',
                      '1,A,B,extra\n', '1,,B\n', '1,A, \n', '"sin cerrar,A,B', '1,A,A\n']:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                self.leer_texto(texto)

    def test_encabezados(self):
        registros, clases = self.leer_texto('identificador,Clase real,Clase estimada\n1,A,B\n')
        self.assertEqual(registros, [('1', 'A', 'B')])
        self.assertEqual(clases, ['A', 'B'])
        self.assertEqual(self.leer_texto('cualquier,otro,nombre\n1,A,B\n', encabezado=True)[0], registros)
        self.assertEqual(self.leer_texto('1,A,B\n', encabezado=False)[0], registros)

    def test_numeros_nombres_y_predicciones_exclusivas(self):
        registros, clases = self.leer_texto('1,0,1\n2,0,2\n', 3)
        self.assertEqual(clases, ['0', '1', '2'])
        self.assertEqual(len(registros), 2)
        self.assertEqual(self.leer_texto('1,gato domestico,perro\n')[1], ['gato domestico', 'perro'])

    def test_archivo_inexistente_extension_y_clases(self):
        with self.assertRaises(OSError):
            leer_csv('/no/existe.csv', 2)
        with self.assertRaises(ValueError):
            leer_csv('archivo.txt', 2)
        for cantidad in [0, 1, -1, '2']:
            with self.subTest(cantidad=cantidad), self.assertRaises(ValueError):
                self.leer_texto('1,A,B\n', cantidad)
        with self.assertRaises(ValueError):
            self.leer_texto('1,A,B\n', 3)

    def test_nombres_salida(self):
        with tempfile.TemporaryDirectory() as carpeta:
            for nombres in [[''], ['A.csv', 'a.csv'], ['../A.csv'], ['A.txt'], ['a/b.csv'], [' a.csv']]:
                with self.subTest(nombres=nombres), self.assertRaises(ValueError):
                    validar_nombres(carpeta, nombres)
            self.assertEqual(len(validar_nombres(carpeta, ['uno.csv', 'dos.csv'])), 2)
        with self.assertRaises(ValueError):
            validar_nombres('/no/existe', ['a.csv'])


if __name__ == '__main__':
    unittest.main()
