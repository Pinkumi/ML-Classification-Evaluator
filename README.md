# Evaluador de modelos de clasificación

Aplicación universitaria para evaluar predicciones existentes en archivos CSV. No entrena modelos. Utiliza Python 3 (3.10 o posterior), Tkinter/ttk, `csv` y `unittest`; todos pertenecen a la biblioteca estándar. Los cálculos están programados manualmente, sin pandas, numpy ni scikit-learn.

## Instalación y ejecución

Desde la carpeta del proyecto:

```bash
python3 main.py
```

En Windows también puede utilizarse `python main.py` o abrir `main.pyw` con doble clic. Se necesita una sesión gráfica y una instalación de Python que incluya Tkinter. En Debian/Ubuntu, si falta Tkinter, instalar el paquete del sistema:

```bash
sudo apt install python3-tk
```

No se necesitan paquetes de pip. La interfaz permite elegir archivos y carpetas, procesar datos y consultar errores sin usar la consola.

## Archivos

- `main.py`: inicia la aplicación.
- `main.pyw`: entrada para abrir la aplicación en Windows sin consola.
- `interfaz.py`: configuración, procesamiento y tablas de resultados.
- `evaluador.py`: evaluación One-vs-Rest, conteos, métricas y matriz.
- `archivos.py`: lectura, validación y exportación CSV.
- `datos/ejemplo_clase.csv`: los 15 registros del ejercicio del profesor.
- `datos/ejemplo_adicional.csv`: seis registros con dos clases.
- `pruebas/`: pruebas de lógica, archivos y acciones del controlador.
- `resultados/`: carpeta predeterminada para las salidas; su contenido generado se excluye de Git.

## Formato del CSV

CSV UTF-8 (con o sin BOM), separado por comas y con exactamente tres columnas en este orden:

```csv
ID-Dato,Clase verdadera,Clase Prediccion
1,A,A
2,A,B
3,B,B
```

Las etiquetas son texto: se aceptan números, letras y nombres. Se eliminan espacios exteriores y se distingue entre mayúsculas y minúsculas. Las clases se detectan tanto en valores verdaderos como predichos y se muestran en orden de aparición. Debe haber al menos un registro y dos clases distintas.

La detección automática reconoce encabezados habituales, como el del ejemplo. Para encabezados con nombres arbitrarios, seleccione **Si** en «El CSV tiene encabezado». Seleccione **No** para forzar que la primera fila se trate como dato. Esta opción evita confundir encabezados desconocidos con datos reales.

## Uso

1. En **Configuracion**, seleccione el CSV, indique la cantidad de clases y cargue los datos. La cantidad indicada debe coincidir con las etiquetas detectadas.
2. Modifique los nombres CSV para cada clase, los resultados generales y la matriz. Los nombres deben ser distintos y no contener rutas. Elija una carpeta existente con permisos de escritura.
3. Abra **Procesamiento** y seleccione un modo.
   - **Paso a paso**: al iniciar se procesa el primer registro. «Siguiente dato» procesa exactamente uno más. «Procesar restantes» continúa por lotes.
   - **Completo**: procesa todos los registros por lotes con `after()`, permitiendo que la ventana atienda eventos.
4. «Terminar» cancela la evaluación y descarta el avance. No exporta resultados parciales. Una nueva ejecución comienza desde el primer registro.
5. Al terminar, consulte **Resultados**: sumatorias, métricas con cuatro decimales, promedios macro y matriz. Las tablas tienen desplazamiento horizontal y vertical.

Ambos modos utilizan el mismo evaluador. La aplicación intenta exportar automáticamente al finalizar y confirma los archivos guardados. Antes de reemplazar archivos existentes solicita confirmación. Si omite la exportación o falla la escritura, los resultados completos permanecen disponibles para volver a intentar con «Guardar resultados». El botón «Guardar matriz en CSV» permite escoger otro nombre para la matriz.

## Criterio de evaluación y métricas

One-vs-Rest compara cada registro contra **cada clase**, considerando esa clase como positiva y todas las demás como negativas:

- **TP**: verdadera y predicha coinciden con la clase.
- **FP**: sólo la predicha coincide.
- **FN**: sólo la verdadera coincide.
- **TN**: ninguna coincide.

Por ejemplo, una predicción B para un registro verdadero A produce FN para A, FP para B y TN para C. Cada registro recibe exactamente una etiqueta por clase.

```text
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
Accuracy  = (TP + TN) / (TP + TN + FP + FN)
F1        = 2 * Precision * Recall / (Precision + Recall)
```

Si un denominador es cero, el resultado es 0. Los resultados generales son el promedio aritmético de cada métrica entre las clases (macro), sin ponderación. La Accuracy macro de One-vs-Rest puede diferir de la proporción de aciertos multiclase.

La matriz multiclase tiene filas de clases verdaderas y columnas de clases predichas. Cada registro aumenta una sola celda; la suma de sus valores coincide con el número de registros. Las tablas individuales One-vs-Rest, en cambio, contienen una evaluación por registro **para cada clase**.

## Archivos generados

Para N clases se exportan N + 2 archivos:

- Un CSV por clase con `ID-Dato,Evaluacion`, conservando el orden del dataset.
- Un CSV de resultados (por defecto `ResultadosFinal.csv`) con secciones de sumatorias, métricas individuales y promedios macro. Contiene valores numéricos, no fórmulas.
- Un CSV de matriz (por defecto `MatrizConfusion.csv`) con encabezados de filas y columnas.

Los archivos se escriben con UTF-8 BOM para facilitar su apertura en hojas de cálculo. Los nombres individuales predeterminados usan índices, para admitir etiquetas que no sean nombres de archivo válidos. Todos son editables. Si ocurre un error durante el reemplazo de destinos, revise el aviso y vuelva a guardar el conjunto completo; la exportación no es una transacción entre archivos.

## Pruebas

```bash
python3 -m unittest discover -s pruebas -v
```

Se ejecutan sin abrir ventanas ni requerir Tkinter. Incluyen el ejercicio de 15 registros, dos y más de tres clases, aciertos y errores completos, divisiones por cero, CSV inválidos, exportación y equivalencia de modos. Las pruebas del controlador sustituyen los widgets por objetos simulados; no reemplazan una revisión visual.

La matriz esperada del ejercicio es:

```text
Real / Prediccion   A  B  C
A                   3  1  1
B                   0  4  1
C                   4  1  0
```

Sus conteos `(TP, TN, FP, FN)` son A `(3, 6, 4, 2)`, B `(4, 8, 2, 1)` y C `(0, 8, 2, 5)`.

## Git

Los cambios están registrados por etapas en la rama `main`. Los datasets de ejemplo están versionados; los CSV generados en `resultados/`, los temporales y los entornos virtuales se excluyen.

El remoto previsto es `https://github.com/Pinkumi/ML-Classification-Evaluator.git`. No se realiza push automáticamente. Después de revisar el proyecto:

```bash
git push -u origin main
```
