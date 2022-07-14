import json

from ..models.errors import *


class Starship:
    def __init__(
        self,
        name="unknown",
        type="unknown",
        TL=0,
        hull=0,
        is_streamlined=False,
        armour=0,
        drive_m=0,
        drive_j=0,
        power_plant=0,
        fuel_capacity=0.0,
        fuel_jump=0,
        fuel_operations=0,
        has_fuel_scoop=False,
        fuel_current=0.0,
        computer=0,
        computer_bis=0,
        sensors=0,
        staterooms=0,
        low_berths=0,
        cargo_capacity=0.0,
        cargo_current=0.0,
    ):
        self.name = name
        self.type = type
        self.TL = TL
        self.hull = hull
        self.is_streamlined = is_streamlined
        self.armour = armour
        self.drive_m = drive_m
        self.drive_j = drive_j
        self.power_plant = power_plant
        self.fuel_capacity = fuel_capacity
        self.fuel_jump = fuel_jump
        self.fuel_operations = fuel_operations
        self.has_fuel_scoop = has_fuel_scoop
        self.fuel_current = fuel_current
        self.computer = computer
        self.computer_bis = computer_bis
        self.sensors = sensors
        self.staterooms = staterooms
        self.low_berths = low_berths
        self.cargo_capacity = cargo_capacity
        self.cargo_current = cargo_current

    def set_attribute(self, name, value):
        """Safely set attributes"""

        if name not in dir(self):
            raise InvalidArgument(f"Unknown attribute {name}")

        t = type(getattr(self, name))

        if t == int:
            try:
                setattr(self, name, int(value))
            except ValueError:
                raise InvalidArgument(f"{name} cannot be converted to an int")
            return

        if t == float:
            try:
                setattr(self, name, float(value))
            except ValueError:
                raise InvalidArgument(f"{name} cannot be converted to a float")
            return

        if t == bool:
            try:
                setattr(self, name, bool(value))
            except ValueError:
                raise InvalidArgument(f"{name} cannot be converted to a bool")
            return

        if t == type(value):
            setattr(self, name, value)
            return

        raise InvalidArgument(f"{name} must be an instance of {type(getattr(self, name))}")

    def __str__(self):

        s = f"""name: {self.name}
cargo: {self.cargo_current}/{self.cargo_capacity}
fuel: {self.fuel_current}/{self.fuel_capacity}
"""
        already_included = set(["name", "cargo_current", "cargo_capacity", "fuel_current", "fuel_capacity"])
        s += "\n".join([f"{i}: {getattr(self, i)}" for i in self.__dict__ if i not in already_included])

        return s