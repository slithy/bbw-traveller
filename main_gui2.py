import tkinter as tk

from cogst5.session_data import BbwSessionData
from cogst5.gui2 import *

class BbwGUI:
    def __init__(self):
        self._session_data, _ = BbwSessionData.load("session_data")
        self.main()

    def main(self):
        self._tk = tk.Tk()
        self._tk.title('Main Window')
        self._ships = BbwObjGUI(master=self._tk, d=self._session_data.fleet())
        self._ships.grid()

        # for s in self._session_data.fleet().values():
        #     self._ships.append( tk.Button(master=self._tk, text=s.name(), command=self.ship ))
        #     self._ships[-1].grid()

    # def ship(self):
    #     self._ship = BbwObjGUI(self._session_data.get_ship_curr())

    def mainloop(self):
        self._tk.mainloop()


if __name__ == '__main__':
    GUI = BbwGUI()
    GUI.mainloop()
