import tkinter as tk

class LiftApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lift Simulation")

        self.current_floor = 0
        self.target_floor = 0
        self.min_floor = -5
        self.max_floor = 10

        self.canvas = tk.Canvas(root, width=200, height=500, bg="white")
        self.canvas.pack()

        self.floor_height = 30
        self.draw_building()

        self.lift = self.canvas.create_rectangle(70, 0, 130, 40, fill="blue")
        self.update_lift_position()

        self.entry = tk.Entry(root)
        self.entry.pack()

        self.button = tk.Button(root, text="Go", command=self.set_target)
        self.button.pack()

        self.status = tk.Label(root, text="Current Floor: 0")
        self.status.pack()

    def draw_building(self):
        for i in range(self.min_floor, self.max_floor + 1):
            y = self.get_y_position(i)
            self.canvas.create_line(0, y, 200, y)
            self.canvas.create_text(20, y - 15, text=str(i))

    def get_y_position(self, floor):
        total_floors = self.max_floor - self.min_floor + 1
        floor_index = self.max_floor - floor
        return floor_index * self.floor_height

    def update_lift_position(self):
        y = self.get_y_position(self.current_floor)
        self.canvas.coords(self.lift, 70, y - 40, 130, y)

    def set_target(self):
        try:
            target = int(self.entry.get())
            if self.min_floor <= target <= self.max_floor:
                self.target_floor = target
                self.move_lift()
        except ValueError:
            pass

    def move_lift(self):
        if self.current_floor < self.target_floor:
            self.current_floor += 1
        elif self.current_floor > self.target_floor:
            self.current_floor -= 1
        else:
            self.status.config(text=f"Stopped at Floor: {self.current_floor}")
            return

        self.update_lift_position()
        self.status.config(text=f"Current Floor: {self.current_floor}")
        self.root.after(500, self.move_lift)


if __name__ == "__main__":
    root = tk.Tk()
    app = LiftApp(root)
    root.mainloop()