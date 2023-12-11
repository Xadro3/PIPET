from tkinter import *
from tkinter import ttk


def display():
    window = Tk()
    window.title("ENTE dev GUI")

    mainframe = ttk.Frame(window, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)


class GUI:
    pass
