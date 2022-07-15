from models.errors import *

from safe_objects import SafeObj

from inventory import Inventory

from utils import safe_conv

class Starship(SafeObj):
    def __init__(self, name="", type="", TL=12, cargo_max=1.0, crew_current=0, passenger_current=0,
                 stateroom_bed_max=1,
                 low_berth_current=0, low_berth_max=1):
        self.set_attr("name", name, str)
        self.set_attr("type", type, str)
        self.set_attr("TL", TL, int)
        self.crew_current=0
        self.passenger_current=0
        self.stateroom_bed_max=1
        self.low_berth_current=0
        self.low_berth_max=1
        self.set_attr("crew_current", crew_current, int)
        self.set_attr("passenger_current", passenger_current, int)
        self.set_attr("stateroom_bed_max", stateroom_bed_max, int)
        self.set_attr("crew_current", crew_current, int)
        self.set_attr("low_berth_current", low_berth_current, int)
        self.set_attr("low_berth_max", low_berth_max, int)

        self.inventory = Inventory(cargo_max)

    def stateroom_bed_current(self):
        return self.crew_current + self.passenger_current

    def _people_status_str(self):
        return f"{self.stateroom_bed_current()}/{self.stateroom_bed_max} ({self.crew_current} c, " \
               f"{self.passenger_current} p) lb: " \
               f"{self.low_berth_current}/{self.low_berth_max}"

    def add_passenger(self, count=1):
        count = safe_conv(count, int)
        self.set_attr("passenger_current", count+self.passenger_current)
        
    def add_crew(self, count=1):
        count = safe_conv(count, int)
        self.set_attr("crew_current", count+self.crew_current)

    def set_attr(self, key, value, t=None):

        if key in ["crew_current", "passenger_current", "low_berth_current"] and value < 0:
            raise InvalidArgument(f"{key} must be non-negative!")

        if key in ["TL", "stateroom_bed_max", "low_berth_max",] and value <= 0:
            raise InvalidArgument(f"{key} must be positive!")
        
        if key == "low_berth_current" and value > self.low_berth_max:
            raise InvalidArgument(f"You cannot fit so many people in low berth. People status:"
                                  f" {self._people_status_str()}")
        
        if key in ["crew_current", "passenger_current"]:
        
            this, other = self.passenger_current, self.crew_current
            if key == "crew_current":
                this, other = other, this

            if value+other > self.stateroom_bed_max:
                raise InvalidArgument(f"You cannot fit these additional people on the starship ({value-this})! Current "
                                      f"people "
                                      f"status: {self._people_status_str()}")


        super().set_attr(key, value, t)

    def __str__(self, is_detailed=False):
        s = f"name: {self.name}\n"
        s += f"people status: {self._people_status_str()}\n"
        s += "inventory:\n"
        s += self.inventory.__str__()

        return s


a = Starship(stateroom_bed_max=5)
a.add_passenger(2)
a.add_passenger(1)
a.add_crew(2)



print(a)


    # def __init__(
    #     self,
    #     name="",
    #     type="",
    #     TL=0,
    #     hull=0,
    #     is_streamlined=False,
    #     armour=0,
    #     drive_m=0,
    #     drive_j=0,
    #     power_plant=0,
    #     fuel_jump=0,
    #     fuel_max=0.0,
    #     fuel_operations=0,
    #     has_fuel_scoop=False,
    #     fuel_current=0.0,
    #     computer=0,
    #     computer_bis=0,
    #     sensors=0,
    #     staterooms=0,
    #     low_berths=0,
    # ):
    #     self.name = name
    #     self.type = type
    #     self.TL = TL
    #     self.hull = hull
    #     self.is_streamlined = is_streamlined
    #     self.armour = armour
    #     self.drive_m = drive_m
    #     self.drive_j = drive_j
    #     self.power_plant = power_plant
    #     self.fuel_capacity = fuel_capacity
    #     self.fuel_jump = fuel_jump
    #     self.fuel_operations = fuel_operations
    #     self.has_fuel_scoop = has_fuel_scoop
    #     self.fuel_current = fuel_current
    #     self.computer = computer
    #     self.computer_bis = computer_bis
    #     self.sensors = sensors
    #     self.staterooms = staterooms
    #     self.low_berths = low_berths
    #     self.cargo_capacity = cargo_capacity
    #     self.cargo_current = cargo_current

    # def set_attribute(self, name, value):
    #     """Safely set attributes"""
    #
    #     if name not in dir(self):
    #         raise InvalidArgument(f"Unknown attribute {name}")
    #
    #     t = type(getattr(self, name))
    #
    #     if t == int:
    #         try:
    #             setattr(self, name, int(value))
    #         except ValueError:
    #             raise InvalidArgument(f"{name} cannot be converted to an int")
    #         return
    #
    #     if t == float:
    #         try:
    #             setattr(self, name, float(value))
    #         except ValueError:
    #             raise InvalidArgument(f"{name} cannot be converted to a float")
    #         return
    #
    #     if t == bool:
    #         try:
    #             setattr(self, name, bool(value))
    #         except ValueError:
    #             raise InvalidArgument(f"{name} cannot be converted to a bool")
    #         return
    #
    #     if t == type(value):
    #         setattr(self, name, value)
    #         return
    #
    #     raise InvalidArgument(f"{name} must be an instance of {type(getattr(self, name))}")

#     def __str__(self):
#
#         s = f"""name: {self.name}
# cargo: {self.cargo_current}/{self.cargo_capacity}
# fuel: {self.fuel_current}/{self.fuel_capacity}
# """
#         already_included = set(["name", "cargo_current", "cargo_capacity", "fuel_current", "fuel_capacity"])
#         s += "\n".join([f"{i}: {getattr(self, i)}" for i in self.__dict__ if i not in already_included])
#
#         return s
