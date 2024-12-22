from collections.abc import Callable
import tkinter as tk
from sudoku import SudokuState, Difficulty
from sudoku_render import SudokuRender
from typing import Optional, Literal
import time

# (row, col, old_value, new_value)
SudokuOperation = tuple[int, int, Optional[int], Optional[int]]

difficulty_options = [d.name for d in Difficulty]
difficulty_map = { d.name: d for d in Difficulty }

class Controller:
    root: tk.Tk
    sudoku: SudokuState
    sudoku_render: SudokuRender
    op_stack: list[SudokuOperation]
    op_stack_listbox: tk.Listbox
    buttons_number: list[tk.Button]
    button_clear: tk.Button
    button_undo: tk.Button
    button_note: tk.Button
    button_note_all: tk.Button
    button_hint: tk.Button
    button_restart: tk.Button
    option_difficulty: tk.OptionMenu
    selected_restart_option: tk.StringVar
    label_timer: tk.Label
    timer_id: Optional[str]
    label_game_state: tk.Label
    time: int
    do_noting: bool
    game_state: Literal["running", "complete", "auto"]

    def __init__(self, root, sudoku, sudoku_render, /, cell_size, bg: str, coord: tuple[int, int]):
        self.root = root
        self.sudoku = sudoku
        self.sudoku_render = sudoku_render
        self.do_noting = False
        self.game_state = "running"
        self.op_stack = []
        self.op_stack_listbox = tk.Listbox(root, font=("Consolas", cell_size // 4), selectmode=tk.NONE)
        self.op_stack_listbox.bind("<Button-1>", lambda _: "break")
        self.__init_controls(root, cell_size, bg, coord)
        self.__init_menu_bar(root)

    def __init_controls(self, root, cell_size, bg, coord):
        self.label_game_state = tk.Label(root, text="", bg=bg, font=("Arial", cell_size // 2))
        self.buttons_number = [tk.Button(root, text=number, command=self.__get_handler_on_click_number(number))
                               for number in range(1, 10)]
        self.button_clear = tk.Button(root, text="清除", command=lambda: self.__clear())
        self.button_undo = tk.Button(root, text="撤销", command=lambda: self.__undo())
        self.button_note = tk.Button(root, text="笔记", command=lambda: self.__note())
        self.button_note_all = tk.Button(root, text="一键笔记", command=lambda: self.__note_all())
        self.button_hint = tk.Button(root, text="提示", command=lambda: self.__hint())
        self.button_restart = tk.Button(root, text="重新开始", command=lambda: self.__restart())
        self.selected_restart_option = tk.StringVar()
        self.selected_restart_option.set(difficulty_options[0])
        self.option_difficulty = tk.OptionMenu(root, self.selected_restart_option, *difficulty_options)
        self.time = -1
        self.timer_id = None
        self.label_timer = tk.Label(root, text="", bg=bg, font=("Arial", cell_size))
        self.__update_time()

        (x, y) = coord
        self.op_stack_listbox.place(x=x + 10 * cell_size, y=y, width=6 * cell_size, height=5 * cell_size)
        self.label_game_state.place(x=x + 13 * cell_size, y=y + 7 * cell_size, anchor="center")
        y += 10 * cell_size
        for i, button in enumerate(self.buttons_number):
            button.place(x=x + i * cell_size, y=y + cell_size, width=cell_size, height=cell_size)
        control_buttons = [self.button_clear, self.button_undo,
                           self.button_note, self.button_note_all,
                           self.button_hint, self.button_restart,
                           self.option_difficulty]
        non_number_button_width = 9 * cell_size // len(control_buttons)
        for button in control_buttons:
            button.place(x=x, y=y, width=non_number_button_width, height=cell_size)
            x += non_number_button_width
        x += non_number_button_width
        self.label_timer.place(x=x, y=y)

    def __show_solution(self, solution: list[tuple[int, int, int]]):
        self.game_state = "auto"
        self.do_noting = False
        self.label_game_state.config(text="自动求解中")
        self.op_stack.clear()
        self.op_stack_listbox.delete(0, tk.END)
        self.__restart_timer()

        for (row, col, val) in solution:
            self.__set_number(row, col, val)
            self.sudoku_render.draw_sudoku()
            time.sleep(0.5)

        assert self.__game_is_complete()


    def __init_menu_bar(self, root):
        menu_bar = tk.Menu(root)
        solver_menu = tk.Menu(menu_bar)
        solver_menu.add_command(label="顺序求解", command=lambda: self.__show_solution(self.sudoku.ord_solve()))
        solver_menu.add_command(label="优化求解", command=lambda: self.__show_solution(self.sudoku.opt_solve()))
        menu_bar.add_cascade(label="自动求解", menu=solver_menu)
        root.config(menu=menu_bar)

    @staticmethod
    def __format_time(time: int) -> str:
        return f"{time // 60:02}:{time % 60:02}"

    def __update_time(self):
        if self.__game_is_complete():
            return
        self.time += 1
        self.label_timer.config(text=Controller.__format_time(self.time))
        self.timer_id = self.root.after(1000, lambda: self.__update_time())

    def __game_is_running(self):
        return self.game_state == "running"

    def __game_is_auto(self):
        return self.game_state == "auto"

    def __game_is_complete(self):
        return self.game_state == "complete"

    def __op_stack_pop(self) -> SudokuOperation:
        self.op_stack_listbox.delete(tk.END)
        return self.op_stack.pop()

    def __op_stack_push(self, op: SudokuOperation):
        self.op_stack_listbox.insert(tk.END, f"{len(self.op_stack) + 1:<4} ({op[0]}, {op[1]}) {op[2]} -> {op[3]}")
        self.op_stack.append(op)
        self.op_stack_listbox.see(tk.END) 

    def __set_number(self, row, col, number):
        self.__op_stack_push((row, col, self.sudoku.get_cell(row, col).number, number))
        self.sudoku.set_cell(row, col, number)
        if self.sudoku.is_solved():
            self.__game_complete()

    def __get_handler_on_click_number(self, number: int) -> Callable[[], None]:
        def handler():
            if not self.__game_is_running():
                return
            selected = self.sudoku_render.get_selected()
            if selected is None:
                return
            (row, col) = selected
            if self.do_noting:
                self.sudoku.add_note(row, col, number)
            else:
                self.__set_number(row, col, number)

            self.sudoku_render.draw_sudoku()
        return handler

    def __clear(self):
        if not self.__game_is_running():
            return
        selected = self.sudoku_render.get_selected()
        if selected is None:
            return
        (row, col) = selected
        if self.do_noting:
            self.sudoku.clr_note(row, col)
        else:
            self.__op_stack_push((row, col, self.sudoku.get_cell(row, col).number, None))
            self.sudoku.clr_cell(row, col)

        self.sudoku_render.draw_sudoku()

    def __undo(self):
        if not self.__game_is_running():
            return
        if len(self.op_stack) == 0:
            return
        (row, col, old_value, _) = self.__op_stack_pop()
        if old_value is None:
            self.sudoku.clr_cell(row, col)
        else:
            self.sudoku.set_cell(row, col, old_value)

        self.sudoku_render.draw_sudoku()

    def __note(self):
        if not self.__game_is_running():
            return
        self.do_noting = not self.do_noting
        self.button_note.config(relief="sunken" if self.do_noting else "raised")

    def __add_all_possible_to_note(self, row, col):
        self.sudoku.clr_note(row, col)
        for n in self.sudoku.getpossible(row, col):
            self.sudoku.add_note(row, col, n)

    def __note_all(self):
        if not self.__game_is_running():
            return
        for r in range(9):
            for c in range(9):
                if self.sudoku.get_cell(r, c).isfixed():
                    continue
                self.__add_all_possible_to_note(r, c)
        self.sudoku_render.draw_sudoku()
                
    def __hint(self):
        if not self.__game_is_running():
            return
        selected = self.sudoku_render.get_selected()
        if selected is None:
            return
        (row, col) = selected
        self.__add_all_possible_to_note(row, col)
        self.sudoku_render.draw_sudoku()

    def __restart_timer(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
        self.time = -1
        self.__update_time()

    def __game_complete(self):
        self.game_state = "complete"
        self.label_game_state.config(text="游戏结束")

    def __restart(self):
        if self.__game_is_auto():
            return
        self.game_state = "running"
        self.do_noting = False
        self.sudoku.restart(difficulty_map[self.selected_restart_option.get()])
        self.sudoku_render.restart()
        self.label_game_state.config(text="")
        self.op_stack.clear()
        self.op_stack_listbox.delete(0, tk.END)
        self.__restart_timer()
