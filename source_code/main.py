import sys

from ui.console_ui import run_console_game
from ui.tkinter_ui import run_gui


if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console_game()
    else:
        run_gui()
