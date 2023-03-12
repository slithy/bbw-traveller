import tkinter as tk

from cogst5.base import BbwObj
from cogst5.item import BbwItem

class BbwEntryGUI(tk.Frame):
    def __init__(self, master, label, getter=None, setter=None, setter_args=[], setter_kwargs={}):
        super().__init__(master=master)

        self._getter = getter
        self._setter = setter
        self._setter_args = setter_args
        self._setter_kwargs = setter_kwargs
        self._add_updates = []
        self._var = tk.StringVar(self)

        self._label = tk.Label(self, text=f"{label}: ")
        self._label.grid(row=0, column=0)

        self._label_var = tk.Label(self, textvariable=self._var)
        self._label_var.grid(row=0, column=1)
        if self._setter:
            self._entry = tk.Entry(self)
            self._entry.bind('<Return>', self.update_obj)
            self._entry.grid(row=0, column=2)

        self.update_GUI()

    def update_GUI(self):
        if self._getter:
            self._var.set(self._getter())
        for i in self._add_updates:
            i()

    def update_obj(self, keypress):
        if self._setter:
            self._setter(self._entry.get(), *self._setter_args, **self._setter_kwargs)
        self._entry.delete(0, tk.END)
        self.update_GUI()


class BbwDictGUI(tk.Frame):
    def __init__(self, master, d):
        super().__init__(master)

        self._master = master
        self._d = d
        self._max_row = 40
        self._add_updates_on_closing = []
        self._add_updates = []

        self._d_frame = tk.Frame(self)
        self._d_frame.grid(row=1, column=2)
        self._d_GUI = {}
        self._var = tk.StringVar(self._d_frame)

        self._commands_frame = tk.Frame(self)
        self._commands_frame.grid(row=0, column=2)
        self._buttons_frame = tk.Frame(self._commands_frame)
        self._buttons_frame.grid()
        self._edit = tk.Button(master=self._buttons_frame, text="edit", command=self.edit_obj)
        self._edit.grid(row=0, column=0)
        self._del = tk.Button(master=self._buttons_frame, text="del", command=self.del_obj)
        self._del.grid(row=0, column=1)
        self._new = tk.Button(master=self._buttons_frame, text="new", command=self.new_obj)
        self._new.grid(row=0, column=2)
        self._entries_frame = tk.Frame(self._commands_frame)
        self._entries_frame.grid()
        self._rename_label = tk.Label(master=self._entries_frame, text="rename: ")
        self._rename_label.grid(row=0, column=0)
        self._rename = tk.Entry(master=self._entries_frame)
        self._rename.bind('<Return>', self.rename_obj)
        self._rename.grid(row=0, column=1)

        self.update_GUI()

    def clear_GUI(self):
        for i in self._d_GUI.values():
            i.destroy()
        self._d_GUI.clear()
        self._var.set("")

    def update_GUI(self):
        self.clear_GUI()
        for k, v in self._d.items():
            idx = len(self._d_GUI)

            text = f"{k}, {v}" if not isinstance(v, BbwObj) else v.name_GUI()

            self._d_GUI[k] = tk.Radiobutton(master=self._d_frame, variable=self._var, value=k, text=text)
            self._d_GUI[k].grid(row = idx%self._max_row, column = int(idx/self._max_row))
            if not idx:
                self._d_GUI[k].invoke()

        for i in self._add_updates:
            i()

    def edit_obj(self, cls=None):
        k = self._var.get()
        if k in self._d and isinstance(self._d[k], dict):
            self._edit_tk = tk.Tk()
            self._edit_obj = BbwDictGUI(master=self._edit_tk, d=self._d[k]) if cls is None else cls(master=self._edit_tk, d=self._d[k])
            self._edit_obj.grid()

    def del_obj(self):
        k = self._var.get()
        if k in self._d:
            del self._d[k]

        self.update_GUI()

    def add_obj(self, k, v):
        self._d[k] = v
        self.update_GUI()
        self._d_GUI[k].invoke()

    def get_new_name(self, base_name):
        name = base_name
        idx = 1
        while name in self._d:
            name, idx = f"{base_name}_{idx}", idx + 1
        return name


    def new_obj(self):
        name = self.get_new_name("new_obj")
        self.add_obj(name, 0)

    def rename_obj(self, keypress):
        new_name = self._rename.get()
        old_name = self._var.get()

        if old_name and new_name not in self._d:
            self._d[new_name] = self._d.pop(old_name)
            self._d[new_name].set_name(new_name)
            self._rename.delete(0, tk.END)

        self.update_GUI()
        self._d_GUI[new_name].invoke()

    def destroy(self):
        for i in self._add_updates_on_closing:
            i()
        super().destroy()

class BbwObjGUI(BbwDictGUI):
    def __init__(self, master, d):
        super().__init__(master=master, d=d)

        self._data_frame = tk.Frame(self)
        self._data_frame.grid(row=1, column=0)
        self._size = BbwEntryGUI(master=self._data_frame, label="size", getter=self._d.size, setter=self._d.set_size)
        self._size.grid()

        self._count_label = tk.Label(master=self._entries_frame, text="set count: ")
        self._count_label.grid(row=1, column=0)
        self._count = tk.Entry(master=self._entries_frame)
        self._count.bind('<Return>', self.set_count_obj)
        self._count.grid(row=1, column=1)

        self._capacity_label = tk.Label(master=self._entries_frame, text="set capacity: ")
        self._capacity_label.grid(row=2, column=0)
        self._capacity = tk.Entry(master=self._entries_frame)
        self._capacity.bind('<Return>', self.set_capacity_obj)
        self._capacity.grid(row=2, column=1)



        self.update_title()

    def update_title(self):
        self._master.title(self._d.name_GUI())

    def edit_obj(self):
        tp = type(self._d[self._var.get()])
        if tp == BbwItem:
            super().edit_obj(cls=BbwItemGUI)

        else:
            super().edit_obj(cls=BbwObjGUI)
        self._edit_obj._add_updates_on_closing.append(self.update_title)

    def set_count_obj(self, keypress):
        new_count = self._count.get()
        name = self._var.get()
        self._d.set_child_count(name, new_count)

        self.update_GUI()
        self._d_GUI[name].invoke()
        self.update_title()
        self._count.delete(0, tk.END)

    def set_capacity_obj(self, keypress):
        new_capacity = self._capacity.get()
        name = self._var.get()
        self._d.set_child_capacity(name, new_capacity)

        self.update_GUI()
        self._d_GUI[name].invoke()
        self.update_title()
        self._capacity.delete(0, tk.END)

    def new_obj(self):
        now = tk.Tk()

        def new_BbwObj():
            name = self.get_new_name("new_obj")
            self.add_obj(name, BbwObj(name=name))
            now.destroy()
        b = tk.Button(master=now, text="obj", command=new_BbwObj)
        b.grid(row=0, column=0)

        def new_BbwItem():
            name = self.get_new_name("new_item")
            self.add_obj(name, BbwItem(name=name))
            now.destroy()
        b = tk.Button(master=now, text="item", command=new_BbwItem)
        b.grid(row=0, column=1)

class BbwItemGUI(BbwObjGUI):
    def __init__(self, master, d):
        super().__init__(master=master, d=d)

        self._value = BbwEntryGUI(master=self._data_frame, label="value", getter=self._d.value,
                                  setter=self._d.set_value)
        self._value.grid()
        self._TL = BbwEntryGUI(master=self._data_frame, label="TL", getter=self._d.TL,
                                  setter=self._d.set_TL)
        self._TL.grid()
        self._armour = BbwEntryGUI(master=self._data_frame, label="armour", getter=self._d.armour,
                                  setter=self._d.set_armour)
        self._armour.grid()
        self._damage = BbwEntryGUI(master=self._data_frame, label="damage", getter=self._d.damage,
                                  setter=self._d.set_damage)
        self._damage.grid()
        self._price_multi = BbwEntryGUI(master=self._data_frame, label="price multi", getter=self._d.price_multi,
                                  setter=self._d.set_price_multi)
        self._price_multi.grid()












class BbwFleetGUI(BbwDictGUI):
    def edit_obj(self):
        super().edit_obj(cls=BbwObjGUI)








