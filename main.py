"""Ejecutar con python3 main.py."""


def main():
    try:
        import tkinter as tk
        from interfaz import Aplicacion
    except ModuleNotFoundError as error:
        if error.name == 'tkinter':
            raise SystemExit('Falta Tkinter. En Debian/Ubuntu instale python3-tk.') from error
        raise
    ventana = tk.Tk()
    Aplicacion(ventana)
    ventana.mainloop()


if __name__ == '__main__':
    main()
