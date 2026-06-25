import tkinter as tk

root = tk.Tk()
root.geometry("800x500")
root.configure(bg="red")

tk.Label(
    root,
    text="Nếu thấy chữ này thì Tkinter vẫn render được",
    bg="yellow",
    fg="blue",
    font=("Arial", 28, "bold")
).pack(pady=100)

root.mainloop()