from dataclasses import dataclass
from typing import Optional, cast
from enum import Enum
import random

@dataclass
class SudokuCell:
    number: Optional[int]
    notes: list[int]
    coord: tuple[int, int]
    is_fixed: bool

    def markfixed(self):
        self.is_fixed = True

    def markunfixed(self):
        self.is_fixed = False

    def isfixed(self) -> bool:
        return self.is_fixed

    def addnote(self, n: int):
        if n in self.notes:
            return
        self.notes.append(n)

    def clrnote(self):
        self.notes.clear()

    def removenote(self, n: int):
        if n in self.notes:
            self.notes.remove(n)


class Difficulty(Enum):
    EASY = 0
    NORMAL = 1
    HARD = 2


mapping_from_difficulty_to_nblank = {
    Difficulty.EASY: 27,
    Difficulty.NORMAL: 36,
    Difficulty.HARD: 54,
}

class SudokuState:
    cells: list[list[SudokuCell]]
    difficulty: Difficulty
    total_blank: int
    residual_blank: int

    def __init__(self, difficulty=Difficulty.EASY):
        self.restart(difficulty)

    def number_is_valid(self, r: int, c: int, n: int):
        if any(cell.number == n for cell in self.cells[r] if cell.coord[1] != c):
            return False

        if any(row[c].number == n for i, row in enumerate(self.cells) if i != r):
            return False

        start_row, start_col = 3 * (r // 3), 3 * (c // 3)
        return not any(self.cells[i][j].number == n
            for i in range(start_row, start_row + 3)
            for j in range(start_col, start_col + 3) if i != r or j != c)

    def getpossible(self, row: int, col: int):
        return [n for n in range(1, 10) if self.number_is_valid(row, col, n) ]

    def __fill_cells(self, row: int, col: int) -> bool:
        if row == 9:
            return True

        numberlist = self.getpossible(row, col) 
        random.shuffle(numberlist)

        next_col = col + 1 if col < 8 else 0
        next_row = row if col < 8 else row + 1

        for n in numberlist:
            self.cells[row][col].number = n
            if self.__fill_cells(next_row, next_col):
                return True

        # all possible numbers fail, reset it to None
        self.cells[row][col].number = None
        return False

    def __next_to_be_filled(self, row, col) -> tuple[int, int]:
        for c in range(col + 1, 9):
            if self.get_cell(row, c).number is None:
                return row, c
        for r in range(row + 1, 9):
            for c in range(0, 9):
                if self.get_cell(r, c).number is None:
                    return r, c
        return 9, 0

    def __ord_solve_aux(self, row, col, solution: list[tuple[int, int, int]]) -> bool:
        if row == 9:
            return True

        possible = self.getpossible(row, col) 

        next_row, next_col = self.__next_to_be_filled(row, col)
        old_value = self.get_cell(row, col).number

        for n in possible:
            self.cells[row][col].number = n
            if self.__ord_solve_aux(next_row, next_col, solution):
                self.get_cell(row, col).number = old_value
                solution.append((row, col, n))
                return True

        # all possible numbers fail, reset it to original value
        self.get_cell(row, col).number = old_value
        return False

    def ord_solve(self) -> list[tuple[int, int, int]]:
        solution = []
        r, c = self.__next_to_be_filled(0, -1)
        self.__ord_solve_aux(r, c, solution)
        solution.reverse()
        return solution

    def __opt_solve_aux_get_optimized_cell(self) -> Optional[tuple[int, int, list[int]]]:
        allpossible = [(r, c, self.getpossible(r, c))
            for r in range(0, 9)
            for c in range(0, 9)
            if self.get_cell(r, c).number is None]
        return min(allpossible, key=lambda t: len(t[2])) if len(allpossible) != 0 else None

    def __opt_solve_aux(self, solution: list[tuple[int, int, int]]) -> bool:
        optimized_cell = self.__opt_solve_aux_get_optimized_cell()
        if optimized_cell is None:
            return True
        
        (r, c, ns) = optimized_cell
        old_value = self.get_cell(r, c).number

        for n in ns:
            self.get_cell(r, c).number = n
            if self.__opt_solve_aux(solution):
                self.get_cell(r, c).number = old_value
                solution.append((r, c, n))
                return True

        self.get_cell(r, c).number = old_value
        return False

    def opt_solve(self) -> list[tuple[int, int, int]]:
        solution = []
        self.__opt_solve_aux(solution)
        solution.reverse()
        return solution

    def __set_blank(self, nblank: int):
        blanks = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(blanks)
        for (r, c) in blanks[:nblank]:
            self.cells[r][c].markunfixed()
            self.cells[r][c].number = None

    # initialize cells with 'nblank' empty cells
    def __init_cells(self, nblank: int):
        self.__fill_cells(0, 0)
        self.__set_blank(nblank)

    def set_cell(self, row: int, col: int, n: int):
        if self.cells[row][col].number is None:
            self.residual_blank -= 1
        self.cells[row][col].number = n

    def get_cell(self, row: int, col: int) -> SudokuCell:
        return self.cells[row][col]

    def clr_cell(self, row: int, col: int):
        assert not self.cells[row][col].isfixed()
        self.residual_blank += 1
        self.cells[row][col].number = None

    def add_note(self, row: int, col: int, n: int):
        self.cells[row][col].addnote(n)

    def remove_note(self, row: int, col: int, n: int):
        self.cells[row][col].removenote(n)

    def clr_note(self, row: int, col: int):
        self.cells[row][col].clrnote()

    def is_solved(self) -> bool:
        if self.residual_blank != 0:
            return False
        return all(self.number_is_valid(r, c, cast(int, self.get_cell(r, c).number))
            for r in range(9)
            for c in range(9)
            if not self.get_cell(r, c).isfixed())

    def restart(self, difficulty: Difficulty):
        self.difficulty = difficulty
        self.total_blank = mapping_from_difficulty_to_nblank[difficulty]
        self.residual_blank = self.total_blank
        self.cells = [[SudokuCell(number=None, notes=[], coord=(i, j), is_fixed=True)
            for j in range(9)]
            for i in range(9)]
        self.__init_cells(self.total_blank)
