import copy
import tkinter as tk

from cogst5.base import BbwObj
from cogst5.item import BbwItem
from cogst5.person import BbwPerson
from cogst5.vehicle import BbwSpaceShip




class BbwEntry():
    def __init__(self, master, label, row, column, getter=None, setter=None, setter_args=[], setter_kwargs={}):
        self._master = master
        self._getter = getter
        self._setter = setter
        self._setter_args = setter_args
        self._setter_kwargs = setter_kwargs
        self._add_updates = []

        self._frame = tk.Frame(self._master)
        self._frame.grid(row=row, column=column)

        self._label_fix = tk.Label(self._frame, text=f"{label}: ")
        self._label_fix.pack(side=tk.LEFT)

        self._sv = tk.StringVar(self._frame)
        self._label = tk.Label(self._frame, textvariable=self._sv)
        self._label.pack(side=tk.LEFT)

        if self._setter:
            self._entry = tk.Entry(self._frame)
            self._entry.bind('<Return>', self.set)
            self._entry.pack(side=tk.LEFT)

        self.update()

    def set(self, keypress=None):
        self._setter(self._entry.get(), *self._setter_args, **self._setter_kwargs)

        self.update()
        self._entry.delete(0, tk.END)

    def update(self):
        if self._getter:
            self._sv.set(self._getter())
        for i in self._add_updates:
            i()

    def add_update(self, v):
        self._add_updates.append(v)

class BbwObjGUI():
    def __init__(self, obj):
        self._obj = obj
        self._tk = tk.Tk()
        self._tk.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.update_title()
        self._max_rows = 20
        self._add_updates = []

        self._size = BbwEntry(master=self._tk, label="size", getter=self._obj.size, setter=self._obj.set_size, row=0, column=0)
        self._size.add_update(self.update_title)


        self._children = {}
        self._children_var = tk.StringVar()
        for name in self._obj.keys():
            self.add_child_button(name)

        self._children_command_frame = tk.Frame(master=self._tk)
        self._children_command_frame.grid(row=0, column=2)
        self._children_rename = BbwEntry(master=self._children_command_frame, label="rename", row=0, column=0, setter=self.children_rename)
        self._children_set_count = BbwEntry(master=self._children_command_frame, label="set count", row=1, column=0, setter=self.children_set_count)
        self._children_set_capacity = BbwEntry(master=self._children_command_frame, label="set capacity", row=2, column=0,
                                             setter=self.children_set_capacity)

        self._children_edit = tk.Button(master=self._children_command_frame, text="edit", command=self.children_edit)
        self._children_edit.grid(row=0, column=1)
        self._children_new_obj = tk.Button(self._children_command_frame, text="new obj", command=self.children_new)
        self._children_new_obj.grid(row=1, column=1)

    def children_new(self):
        self._new_tk = tk.Tk()
        self._children_new_obj = tk.Button(self._new_tk, text="new base obj", command=lambda: self.children_new_obj(BbwObj, "new_obj"))
        self._children_new_obj.grid(row=0, column=0)
        self._children_new_item = tk.Button(self._new_tk, text="new item", command=lambda: self.children_new_obj(BbwItem, "new_item"))
        self._children_new_item.grid(row=1, column=0)
        self._children_new_person = tk.Button(self._new_tk, text="new person", command=lambda: self.children_new_obj(BbwPerson, "new_person"))
        self._children_new_person.grid(row=0, column=1)
        self._children_new_ship = tk.Button(self._new_tk, text="new ship", command=lambda: self.children_new_obj(BbwSpaceShip, "new_ship"))
        self._children_new_ship.grid(row=1, column=1)

    def children_new_obj(self, cls, base_name):
        name = base_name
        i = 0
        while name in self._obj:
            name, i = base_name + '_' + str(i), i+1
        new_obj = cls(name=name)


        self._obj.dist_obj(new_obj)
        self.add_child_button(new_obj.name())
        self._new_tk.destroy()

    def add_child_button(self, name, row=None, column=None):
        button = tk.Radiobutton(master=self._tk, variable=self._children_var, value=name,
                                command=lambda name=name: self._children_var.set(name))
        self._children[name] = button
        n = len(self._children)
        if row is None:
            row = n % self._max_rows
        if column is None:
            column = int(n / self._max_rows) + 2
        self._children[name].grid(row=row, column=column)
        button.invoke()
        self.update_child_button(button, name)


    @staticmethod
    def get_title(obj):
        return f"{obj.count()}, {obj.name()}, {obj.status()}"

    def update_title(self):
        self._tk.title(BbwObjGUI.get_title(self._obj))

    def children_rename(self, keypress):
        old_name = self._children_var.get()
        new_name = self._children_rename._entry.get()

        self._obj.rename_obj(old_name, new_name)
        row = self._children[old_name].grid_info()['row']
        column = self._children[old_name].grid_info()['column']
        self._children[old_name].destroy()
        self.add_child_button(new_name, row=row, column=column)

    def children_set_count(self, keypress):
        name = self._children_var.get()
        obj = self._obj[name]
        new_count = int(self._children_set_count._entry.get())
        if new_count == obj.count() or new_count < 0:
            return
        if new_count < obj.count():
            self._obj.del_obj(name, obj.count()-new_count)
            if new_count == 0:
                self._children[name].destroy()
                del self._children[name]
            else:
                self.update_child_button(self._children[name], name)
        else:
            new_obj = copy.deepcopy(obj)
            new_obj.set_count(new_count - obj.count())
            self._obj.dist_obj(new_obj)
            self.update_child_button(self._children[name], name)
        self.update_title()

    def children_set_capacity(self, keypress):
        name = self._children_var.get()
        obj = self._obj[name]
        new_capacity = float(self._children_set_capacity._entry.get())

        new_obj = copy.deepcopy(obj)
        new_obj.set_capacity(new_capacity)

        if new_obj.capacity() > obj.capacity() + self._obj.free_space():
            return

        obj.set_capacity(new_capacity)
        self.update_child_button(self._children[name], name)
        self.update_title()

    def children_edit(self):
        name = self._children_var.get()

        if type(self._obj[name]) == BbwObj:
            self._edit = BbwObjGUI(self._obj[name])
        elif type(self._obj[name]) == BbwItem:
            self._edit = BbwItemGUI(self._obj[name])
        elif type(self._obj[name]) == BbwPerson:
            self._edit = BbwPersonGUI(self._obj[name])
        elif type(self._obj[name]) == BbwSpaceShip:
            self._edit = BbwSpaceShipGUI(self._obj[name])
        else:
            return
        self._edit.add_update(self.update_title)
        self._edit.add_update(lambda: self.update_child_button(self._children[name], name))

    def update_child_button(self, button, name):
        button.config(text=BbwObjGUI.get_title(self._obj[name]))
        button.config(value=name)

    def add_update(self, v):
        self._add_updates.append(v)

    def on_closing(self):
        for i in self._add_updates:
            i()
        self._tk.destroy()

class BbwItemGUI(BbwObjGUI):
    def __init__(self, obj):
        super().__init__(obj)

        self._value = BbwEntry(master=self._tk, label="value", getter=self._obj.value, setter=self._obj.set_value, row=1, column=0)
        self._TL = BbwEntry(master=self._tk, label="TL", getter=self._obj.TL, setter=self._obj.set_TL,
                               row=2, column=0)
        self._armour = BbwEntry(master=self._tk, label="armour", getter=self._obj.armour, setter=self._obj.set_armour,
                               row=3, column=0)
        self._damage = BbwEntry(master=self._tk, label="damage", getter=self._obj.damage, setter=self._obj.set_damage,
                               row=4, column=0)
        self._price_multi = BbwEntry(master=self._tk, label="price multi", getter=self._obj.price_multi, setter=self._obj.set_price_multi,
                                row=5, column=0)

class BbwPersonGUI(BbwObjGUI):
    def __init__(self, obj):
        super().__init__(obj)

        self._upp = BbwEntry(master=self._tk, label="upp", getter=self._obj.upp, setter=self._obj.set_upp,
                             row=1, column=0)
        self._upp.add_update(self.update_stats)
        self._upp.add_update(self.update_title)
        self._salary_ticket = BbwEntry(master=self._tk, label="salary/ticket", getter=self._obj.salary_ticket, setter=self._obj.set_salary_ticket,
                             row=2, column=0)
        self._reinvest = BbwEntry(master=self._tk, label="reinvest", getter=self._obj.reinvest,
                                       setter=self._obj.set_reinvest,
                                       row=3, column=0)

        self._skill_rank_buttons_frame = tk.Frame(self._tk)
        self._skill_rank_buttons_frame.grid(row=0, column=1)
        self._skill_check = tk.Button(self._skill_rank_buttons_frame, text="skill check", command=self.skill_check)
        self._skill_check.grid(row=0, column=0)
        self._skill_new = BbwEntry(master=self._skill_rank_buttons_frame, label="new skill", getter=None,
                                   setter=self.set_rank,
                                   row=0, column=1)
        self._skill_check_var = tk.StringVar(self._skill_rank_buttons_frame)
        self._skill_check_label = tk.Label(self._skill_rank_buttons_frame, textvariable=self._skill_check_var)
        self._skill_check_label.grid(row=1, column=0)
        self._skill_check_del = tk.Button(self._skill_rank_buttons_frame, text="del skill", command=self.del_skill_rank)
        self._skill_check_del.grid(row=1, column=1)

        self._stats_frame = tk.Frame(self._tk)
        self._stats_frame.grid(row=1, column=1)
        self._stats_var = tk.StringVar(self._stats_frame)
        self._stats = {}
        for idx, name in enumerate(["STR", "DEX", "END", "PSI", "INT", "EDU", "SOC"]):
            self.add_stat_skill_rank(master=self._stats_frame, row=idx%4, column=int(idx/4), d=self._stats, var =self._stats_var, name=name, update=self.update_stats_button)

        self._skill_rank_frame = tk.Frame(self._tk)
        self._skill_rank_frame.grid(row=2, column=1)
        self._skill_rank_var = tk.StringVar(self._skill_rank_frame)
        self._skill_rank = {}
        self._skill_rank_max_row = 30
        self.update_skill_rank()

    def del_skill_rank(self):
        name = self._skill_rank_var.get()
        self._obj.set_rank(f"('{name}', None)")
        self.update_skill_rank()

    def update_skill_rank(self):
        for k in self._skill_rank:
            self._skill_rank[k].destroy()
        self._skill_rank.clear()

        idx = 0
        for k, v in self._obj.skill_rank().items():
            self.add_stat_skill_rank(master=self._skill_rank_frame, row=idx % self._skill_rank_max_row, column=int(idx / self._skill_rank_max_row), d=self._skill_rank,
                                     var=self._skill_rank_var, name=k, update=self.update_skill_rank_button)
            idx += 1


    def set_rank(self, v):
        vl = v.split(',')

        val = int(vl[-1])
        name = ', '.join(vl[:len(vl)-1])
        if val > 4:
            self._obj.set_rank(name, val)
        else:
            self._obj.set_skill(name, val)
        self.update_skill_rank()

    def skill_check(self):
        res = self._obj.skill_check(skill=self._skill_rank_var.get(), chosen_stat=self._stats_var.get())[1]
        self._skill_check_var.set(str(res))


    def add_stat_skill_rank(self, master, row, column, d, var, name, update):
        d[name] = tk.Radiobutton(master=master, variable=var, value=name,
                                command=lambda name=name: var.set(name))
        d[name].grid(row=row, column=column)
        d[name].invoke()
        update(d[name], name)

    def update_stats_button(self, button, name):
        stat = getattr(self._obj, name)()
        text = f"{name} ({-3})" if not stat else f"{name} ({stat[1]})"

        button.config(text=text)
        button.config(value=name)

    def update_skill_rank_button(self, button, name):
        v = self._obj.skill_rank()[name]
        text = f"{name} ({v})"

        button.config(text=text)
        button.config(value=name)

    def update_stats(self):
        for k, v in self._stats.items():
            self.update_stats_button(v, k)


class BbwSpaceShipGUI(BbwObjGUI):
    pass