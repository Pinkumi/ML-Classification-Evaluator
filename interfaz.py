"""Ventanas y tablas del evaluador de clasificacion."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from archivos import leer_csv, validar_nombres, exportar_resultados, filas_matriz, escribir_csv
from evaluador import Evaluador


class Aplicacion:
    def __init__(self, ventana):
        self.ventana = ventana
        ventana.title('Evaluador de modelos de clasificacion')
        ventana.geometry('1050x760')
        ventana.minsize(760, 540)
        self.registros, self.clases = [], []
        self.evaluador = None
        self.activo = False
        self.tarea = None
        self.ruta = tk.StringVar()
        self.cantidad = tk.StringVar(value='3')
        self.encabezado = tk.StringVar(value='Automatico')
        self.carpeta = tk.StringVar(value=str(Path(__file__).parent / 'resultados'))
        self.nombre_final = tk.StringVar(value='ResultadosFinal.csv')
        self.nombre_matriz = tk.StringVar(value='MatrizConfusion.csv')
        self.modo = tk.StringVar(value='Paso a paso')
        self.estado = tk.StringVar(value='Seleccione y valide un archivo CSV.')
        self.detalle = tk.StringVar(value='Sin registros procesados.')
        self.nombres = {}
        self.libro = ttk.Notebook(ventana)
        self.libro.pack(fill='both', expand=True, padx=12, pady=12)
        self.configuracion = self.pagina('Configuracion')
        self.procesamiento = self.pagina('Procesamiento')
        self.resultados = self.pagina('Resultados')
        self.crear_configuracion()
        self.crear_procesamiento()
        self.crear_resultados()
        ttk.Label(ventana, textvariable=self.estado, wraplength=1000).pack(fill='x', padx=12, pady=6)
        ventana.protocol('WM_DELETE_WINDOW', self.cerrar)

    def pagina(self, titulo):
        marco = ttk.Frame(self.libro, padding=12)
        self.libro.add(marco, text=titulo)
        return marco

    def campo(self, marco, etiqueta, variable, fila):
        ttk.Label(marco, text=etiqueta).grid(row=fila, column=0, sticky='w', padx=4, pady=5)
        ttk.Entry(marco, textvariable=variable).grid(row=fila, column=1, sticky='ew', padx=4)
        marco.columnconfigure(1, weight=1)

    def crear_configuracion(self):
        marco = self.configuracion
        self.campo(marco, 'Archivo CSV', self.ruta, 0)
        ttk.Button(marco, text='Seleccionar CSV', command=self.seleccionar_csv).grid(row=0, column=2)
        self.campo(marco, 'Cantidad de clases', self.cantidad, 1)
        ttk.Label(marco, text='El CSV tiene encabezado').grid(row=2, column=0, sticky='w')
        ttk.Combobox(marco, textvariable=self.encabezado, values=['Automatico', 'Si', 'No'],
                     state='readonly').grid(row=2, column=1, sticky='ew')
        ttk.Button(marco, text='Cargar y validar datos', command=self.cargar).grid(row=3, column=1, pady=8)
        self.etiquetas = ttk.Label(marco, text='Clases detectadas: ninguna', wraplength=700)
        self.etiquetas.grid(row=4, column=0, columnspan=3, sticky='w')
        self.campos_clases = ttk.Frame(marco)
        self.campos_clases.grid(row=5, column=0, columnspan=3, sticky='nsew', pady=8)
        marco.rowconfigure(5, weight=1)
        self.campo(marco, 'Archivo de resultados', self.nombre_final, 6)
        self.campo(marco, 'Archivo de matriz', self.nombre_matriz, 7)
        self.campo(marco, 'Carpeta de salida', self.carpeta, 8)
        ttk.Button(marco, text='Escoger carpeta', command=self.seleccionar_carpeta).grid(row=8, column=2)
        ttk.Label(marco, text='Seleccione Si para encabezados con nombres personalizados.').grid(
            row=9, column=0, columnspan=3, sticky='w', pady=5)

    def crear_procesamiento(self):
        marco = self.procesamiento
        opciones = ttk.Frame(marco)
        opciones.pack(fill='x')
        ttk.Combobox(opciones, textvariable=self.modo, values=['Paso a paso', 'Completo'],
                     state='readonly', width=18).pack(side='left', padx=4)
        self.iniciar_boton = ttk.Button(opciones, text='Iniciar evaluacion', command=self.iniciar, state='disabled')
        self.iniciar_boton.pack(side='left', padx=4)
        self.siguiente = ttk.Button(opciones, text='Siguiente dato', command=self.paso, state='disabled')
        self.siguiente.pack(side='left', padx=4)
        self.restantes = ttk.Button(opciones, text='Procesar restantes', command=self.procesar_lote, state='disabled')
        self.restantes.pack(side='left', padx=4)
        self.terminar = ttk.Button(opciones, text='Terminar', command=self.cancelar, state='disabled')
        self.terminar.pack(side='left', padx=4)
        self.progreso = ttk.Progressbar(marco)
        self.progreso.pack(fill='x', pady=14)
        ttk.Label(marco, textvariable=self.detalle, wraplength=900).pack(anchor='w', pady=8)
        self.tabla_dato = self.tabla(marco, ['Clase', 'Evaluacion'])

    def tabla(self, marco, columnas):
        contenedor = ttk.Frame(marco)
        contenedor.pack(fill='both', expand=True, pady=5)
        tabla = ttk.Treeview(contenedor, columns=columnas, show='headings', height=7)
        for columna in columnas:
            tabla.heading(columna, text=columna)
            tabla.column(columna, width=max(110, len(str(columna)) * 9), stretch=False)
        vertical = ttk.Scrollbar(contenedor, orient='vertical', command=tabla.yview)
        horizontal = ttk.Scrollbar(contenedor, orient='horizontal', command=tabla.xview)
        tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tabla.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)
        return tabla

    def crear_resultados(self):
        self.resumen = ttk.Label(self.resultados, text='Complete una evaluacion para ver los resultados.')
        self.resumen.pack(anchor='w')
        acciones = ttk.Frame(self.resultados)
        acciones.pack(fill='x', pady=4)
        self.guardar_boton = ttk.Button(acciones, text='Guardar resultados', command=self.guardar, state='disabled')
        self.guardar_boton.pack(side='left', padx=4)
        self.matriz_boton = ttk.Button(acciones, text='Guardar matriz en CSV', command=self.guardar_matriz, state='disabled')
        self.matriz_boton.pack(side='left', padx=4)
        libro = ttk.Notebook(self.resultados)
        libro.pack(fill='both', expand=True)
        paneles = []
        for titulo in ['Sumatorias', 'Metricas y promedios macro', 'Matriz de confusion']:
            panel = ttk.Frame(libro, padding=8)
            libro.add(panel, text=titulo)
            paneles.append(panel)
        self.tabla_conteos = self.tabla(paneles[0], ['Clase', 'TP', 'TN', 'FP', 'FN'])
        self.tabla_metricas = self.tabla(paneles[1], ['Clase', 'Precision', 'Recall', 'Accuracy', 'F1'])
        ttk.Label(paneles[2], text='Filas: clases verdaderas. Columnas: clases predichas.').pack(anchor='w')
        self.panel_matriz = paneles[2]
        self.tabla_matriz = self.tabla(paneles[2], ['Real / Prediccion'])

    def seleccionar_csv(self):
        ruta = filedialog.askopenfilename(title='Seleccionar CSV', filetypes=[('Archivos CSV', '*.csv')])
        if ruta:
            self.ruta.set(ruta)

    def seleccionar_carpeta(self):
        ruta = filedialog.askdirectory(title='Seleccionar carpeta de salida')
        if ruta:
            self.carpeta.set(ruta)

    def cargar(self):
        if self.activo:
            messagebox.showinfo('Evaluacion activa', 'Termine la evaluacion antes de cargar otro archivo.')
            return
        try:
            opciones = {'Automatico': None, 'Si': True, 'No': False}
            registros, clases = leer_csv(self.ruta.get(), int(self.cantidad.get()), opciones[self.encabezado.get()])
        except (ValueError, OSError) as error:
            messagebox.showerror('No se pudo cargar el archivo', str(error))
            return
        self.registros, self.clases = registros, clases
        self.evaluador = None
        self.guardar_boton.config(state='disabled')
        self.matriz_boton.config(state='disabled')
        self.nombres = {}
        for widget in self.campos_clases.winfo_children():
            widget.destroy()
        lienzo = tk.Canvas(self.campos_clases, height=160, highlightthickness=0)
        barra = ttk.Scrollbar(self.campos_clases, orient='vertical', command=lienzo.yview)
        lienzo.configure(yscrollcommand=barra.set)
        barra.pack(side='right', fill='y')
        lienzo.pack(side='left', fill='both', expand=True)
        interior = ttk.Frame(lienzo)
        elemento = lienzo.create_window((0, 0), window=interior, anchor='nw')
        interior.bind('<Configure>', lambda evento: lienzo.configure(scrollregion=lienzo.bbox('all')))
        lienzo.bind('<Configure>', lambda evento: lienzo.itemconfigure(elemento, width=evento.width))
        for indice, clase in enumerate(clases):
            variable = tk.StringVar(value=f'evaluacion_{indice + 1}.csv')
            self.nombres[clase] = variable
            self.campo(interior, f'Clase {clase}', variable, indice)
        self.etiquetas.config(text='Clases detectadas: ' + ', '.join(clases))
        self.estado.set(f'{len(registros)} registros cargados. Configure los nombres y abra Procesamiento.')
        self.iniciar_boton.config(state='normal')

    @staticmethod
    def llenar(tabla, filas):
        tabla.delete(*tabla.get_children())
        for fila in filas:
            tabla.insert('', 'end', values=fila)

    def iniciar(self):
        pass

    def paso(self):
        pass

    def procesar_lote(self):
        pass

    def cancelar(self):
        pass

    def guardar(self):
        pass

    def guardar_matriz(self):
        pass

    def cerrar(self):
        self.ventana.destroy()
