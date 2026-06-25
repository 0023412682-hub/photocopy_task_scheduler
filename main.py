import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"

from ui.app import PhotocopySchedulerApp
import ui.app

print("Đang dùng app.py tại:", ui.app.__file__)


def print_widget_tree(widget, level=0):
    indent = "  " * level

    try:
        bg = widget.cget("bg")
    except Exception:
        bg = ""


    for child in widget.winfo_children():
        print_widget_tree(child, level + 1)


if __name__ == "__main__":
    app = PhotocopySchedulerApp()

    app.update_idletasks()

    # Đợi giao diện render xong rồi mới in cây widget
    app.after(500, lambda: print_widget_tree(app))

    app.mainloop()