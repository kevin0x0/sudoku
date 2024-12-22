import tkinter as tk
from enum import Enum
from sudoku import Difficulty, SudokuState
import sudoku_render as sr
import controller as ctl

class color(Enum):
    BLACK = "#000000"
    HINT = '#6D2DFA'
    SILVER = '#FFFFFF'
    NUMBER = '#6D2DFA'
    WHITE = "#FFFFFF" 
    ORANGE = '#FF8C00'
    RED = "#C80000"
    YELLOW = "#FAE067"
    GREY = '#808080'
    PURPLE = "#FF99FF"
    DEEP_PURPLE = "#FF66FF"

root = tk.Tk()
root.title("数独")
cell_size = 50
width, height = cell_size * 16, cell_size * 12
root.geometry(f'{width}x{height}')
canvas = tk.Canvas(root, background=color.ORANGE.value,
                   highlightthickness=0)
canvas.place(x=0, y=0, width=width, height=height, anchor=tk.NW)

sudoku = SudokuState(difficulty=Difficulty.EASY)
sudoku_render = sr.SudokuRender(canvas, sudoku,
                                cell_size=cell_size,
                                cell_color1=color.WHITE.value,
                                cell_color2=color.YELLOW.value,
                                cell_color_selected=color.DEEP_PURPLE.value,
                                cell_color_selected_row=color.PURPLE.value,
                                cell_color_selected_col=color.PURPLE.value,
                                border_color=color.ORANGE.value,
                                num_color_fixed=color.BLACK.value,
                                num_color_valid=color.GREY.value,
                                num_color_invalid=color.RED.value)
ctrl = ctl.Controller(root, sudoku, sudoku_render, cell_size=cell_size, bg=color.ORANGE.value, coord=(0, 0))

sudoku_render.draw_sudoku()
root.mainloop()
