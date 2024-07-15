class Vehicle:
    def __init__(self):
        self.name = "Ford Icon"
        self.vehicle_num = 'TS08JU2299'
        self.colour = "Red"
        self.type = "Manual"
        self.drive = "Four Wheel"

    def car(self):
        print("It is a Ford Icon car.")

    def get_colour(self):
        print("Colour:", self.colour)

    def get_type(self):
        print("Type:", self.type)

    def get_drive(self):
        print("Drive:", self.drive)

    def get_vehicle_num(self):
        print("Vehicle Number:", self.vehicle_num)

vl = Vehicle()
vl.get_colour()
vl.get_type()
vl.get_drive()
vl.get_vehicle_num()

