"""Comprueba las acciones del controlador sin Tkinter ni pantalla."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch
from evaluador import Evaluador
from archivos import leer_csv


class PruebasControlador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raiz = Path(__file__).resolve().parents[1]
        especificacion = importlib.util.spec_from_file_location('interfaz_prueba', raiz / 'interfaz.py')
        modulo = importlib.util.module_from_spec(especificacion)
        with patch.dict(sys.modules, {'tkinter': MagicMock()}):
            especificacion.loader.exec_module(modulo)
        cls.aplicacion = modulo.Aplicacion
        cls.registros, cls.clases = leer_csv(raiz / 'datos/ejemplo_clase.csv', 3)

    def controlador(self):
        aplicacion = self.aplicacion.__new__(self.aplicacion)
        aplicacion.evaluador = Evaluador(self.registros, self.clases)
        aplicacion.activo = True
        aplicacion.tarea = None
        aplicacion.ventana = MagicMock()
        aplicacion.siguiente = MagicMock()
        aplicacion.restantes = MagicMock()

        def actualizar(evaluacion):
            self.assertIsNotNone(evaluacion)
            if aplicacion.evaluador.terminado:
                aplicacion.activo = False
        aplicacion.actualizar_registro = actualizar
        return aplicacion

    def test_siguiente_solo_un_registro_y_mismos_resultados(self):
        paso = self.controlador()
        for indice in range(15):
            paso.paso()
            self.assertEqual(paso.evaluador.posicion, indice + 1)
        completo = self.controlador()
        completo.procesar_lote()
        self.assertEqual(paso.evaluador.resultados(), completo.evaluador.resultados())

    def test_lotes_programan_continuacion(self):
        aplicacion = self.controlador()
        aplicacion.evaluador = Evaluador(self.registros * 100, self.clases)
        aplicacion.procesar_lote()
        self.assertGreater(aplicacion.evaluador.posicion, 0)
        self.assertLess(aplicacion.evaluador.posicion, 1500)
        aplicacion.ventana.after.assert_called_once_with(1, aplicacion.continuar_lote)
        posicion = aplicacion.evaluador.posicion
        aplicacion.paso()
        self.assertEqual(aplicacion.evaluador.posicion, posicion)

    def test_cancelar_descarta_acumulador_y_callback(self):
        aplicacion = self.controlador()
        for nombre in ('terminar', 'guardar_boton', 'matriz_boton', 'iniciar_boton',
                       'libro', 'configuracion', 'resultados', 'progreso', 'tabla_dato',
                       'detalle', 'estado'):
            setattr(aplicacion, nombre, MagicMock())
        aplicacion.registros = self.registros
        aplicacion.tarea = 'pendiente'
        aplicacion.evaluador.avanzar()
        aplicacion.cancelar()
        aplicacion.ventana.after_cancel.assert_called_once_with('pendiente')
        self.assertIsNone(aplicacion.evaluador)
        self.assertFalse(aplicacion.activo)
        self.assertIsNone(aplicacion.tarea)
