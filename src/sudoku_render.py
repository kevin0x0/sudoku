import tkinter as tk
from sudoku import SudokuState
from typing import Optional

class SudokuRender:
    canvas: tk.Canvas
    sudokustate: SudokuState
    coord: tuple[int, int]
    cell_size: int
    size: int
    cell_color1: str
    cell_color2: str
    cell_color_selected: str
    cell_color_selected_row: str
    cell_color_selected_col: str
    border_color: str
    num_color_fixed: str
    num_color_valid: str
    num_color_invalid: str
    selected_cell: Optional[tuple[int, int]]

    def __init__(self, canvas: tk.Canvas, sudokustate: SudokuState,
                 cell_size,
                 coord,
                 cell_color1,
                 cell_color2,
                 cell_color_selected,
                 cell_color_selected_row,
                 cell_color_selected_col,
                 border_color,
                 num_color_fixed,
                 num_color_valid,
                 num_color_invalid):
        self.canvas = canvas
        self.sudokustate = sudokustate
        self.coord = coord
        self.cell_size = cell_size
        self.size = cell_size * 9
        self.cell_color1 = cell_color1
        self.cell_color2 = cell_color2
        self.cell_color_selected = cell_color_selected
        self.cell_color_selected_row = cell_color_selected_row
        self.cell_color_selected_col = cell_color_selected_col
        self.border_color = border_color
        self.num_color_fixed = num_color_fixed
        self.num_color_valid = num_color_valid
        self.num_color_invalid = num_color_invalid
        self.selected_cell = None

        def on_click(event):
            x, y = event.x - self.coord[0], event.y - self.coord[1]
            if not (0 <= x < self.size and 0 <= y < self.size):
                return
            selected_row, selected_col = y // self.cell_size, x // self.cell_size
            if self.sudokustate.get_cell(selected_row, selected_col).isfixed():
                return
            new_value = (selected_row, selected_col)
            self.selected_cell = new_value if self.selected_cell != new_value else None
            self.draw_sudoku()

        canvas.bind("<Button-1>", on_click)

    def __clear(self):
        self.canvas.delete("all")

    def __draw_notes(self, row: int, col: int):
        cell = self.sudokustate.get_cell(row, col)
        x0, y0 = self.__get_cellpos(row, col)
        x0, y0 = x0 + self.cell_size // 6, y0 + self.cell_size // 6
        for number in cell.notes:
            num_color = self.num_color_valid
            offset_x, offset_y = self.__get_mini_number_offset(number)
            self.canvas.create_text(x0 + offset_x, y0 + offset_y, text=number, anchor="center",
                                    font=("Arial", self.cell_size // 5, "bold"), fill=num_color)

    def __draw_fixed(self, row: int, col: int):
        cell = self.sudokustate.get_cell(row, col)
        assert cell.number is not None
        number = cell.number
        x0, y0 = self.__get_cellpos(row, col)
        x0, y0 = x0 + self.cell_size // 2, y0 + self.cell_size // 2
        self.canvas.create_text(x0, y0, text=number, anchor="center",
                                font=("Arial", self.cell_size // 2, "bold"), fill=self.num_color_fixed)

    def __draw_number(self, row: int, col: int, number: int):
        color = self.num_color_valid if self.sudokustate.number_is_valid(row, col, number) else self.num_color_invalid
        x0, y0 = self.__get_cellpos(row, col)
        x0, y0 = x0 + self.cell_size // 2, y0 + self.cell_size // 2
        self.canvas.create_text(x0, y0, text=number, anchor="center",
                                font=("Arial", self.cell_size // 2, "bold"), fill=color)

    def __draw_cell_content(self, row: int, col: int):
        cell = self.sudokustate.get_cell(row, col)
        if cell.isfixed():
            self.__draw_fixed(row, col)
            return

        cell = self.sudokustate.get_cell(row, col)
        if cell.number is not None:
            self.__draw_number(row, col, cell.number)
        else:
            self.__draw_notes(row, col)

    def __get_mini_number_offset(self, number: int) -> tuple[int, int]:
        mini_cell_x, mini_cell_y = (number - 1) % 3, (number - 1) // 3
        mini_number_size = (self.cell_size // 3)
        return mini_number_size * mini_cell_x, mini_number_size * mini_cell_y

    def __get_cellpos(self, row: int, col: int) -> tuple[int, int]:
        return self.coord[0] + self.cell_size * col, self.coord[1] + self.cell_size * row

    def __get_cell_color(self, row: int, col: int) -> str:
        if self.selected_cell is not None:
            if row == self.selected_cell[0] and col == self.selected_cell[1]:
                return self.cell_color_selected
            if row == self.selected_cell[0]:
                return self.cell_color_selected_row
            if col == self.selected_cell[1]:
                return self.cell_color_selected_col

        return self.cell_color1 if (row // 3 + col // 3) % 2 == 0 else self.cell_color2

    def __draw_cell(self, row: int, col: int):
        x0, y0 = self.__get_cellpos(row, col)
        x1, y1 = x0 + self.cell_size, y0 + self.cell_size
        fill_color = self.__get_cell_color(row, col)
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill_color, outline=self.border_color)
        self.__draw_cell_content(row, col)


    def draw_sudoku(self):
        self.__clear()
        for row in range(9):
            for col in range(9):
                self.__draw_cell(row, col)
        self.canvas.update()

    def get_selected(self) -> Optional[tuple[int, int]]:
        return self.selected_cell
    
    def restart(self):
        self.selected_cell = None
        self.__clear()
        self.draw_sudoku()
