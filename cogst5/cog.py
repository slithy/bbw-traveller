import discord
from discord.ext import commands
from cogst5.library import Library
import json
import jsonpickle
from os.path import basename
import time

from cogst5.models.errors import *

from cogst5.session_data import BbwSessionData
from cogst5.base import *
from cogst5.person import *
from cogst5.vehicle import *
from cogst5.company import *
from cogst5.item import *
from cogst5.world import *


jsonpickle.set_encoder_options("json", sort_keys=True)


class Game(commands.Cog):
    """Traveller 5 commands."""

    def __init__(self, bot):
        self.bot = bot
        self.library = Library()
        self.session_data = BbwSessionData()

    async def send(self, ctx, msg):
        """Split long messages to workaround the discord limit"""

        msg = "__                                                                          __\n" + msg

        max_length = 2000

        if len(msg) <= max_length:
            await ctx.send(msg)
        else:
            s = msg.split("\n")

            j = 0
            l = 0
            for i in range(len(s)):
                newl = l + len(s[i]) + (l != 0)
                if newl <= max_length:
                    l = newl
                else:
                    token = "\n".join(s[j:i])
                    await ctx.send(token)
                    j = i
                    l = len(s[i])

            last_line = "\n".join(s[j:])
            await ctx.send(last_line)

    # ==== commands ====
    @commands.command(name="library_data", aliases=["library", "lib", "l"])
    async def query_library(self, ctx, search_term: str, *args):
        """*Query ship Library Database*

        In a universe with no faster-than-light communication, there is no Galactic Internet. Every ship therefore carries its own database of information about a wide variety of subjects: worlds, lifeforms, corporations, politics, history, *etc.* Almost all ships in Traveller have this database in the form of the **Library/0** program. The Library database is periodically updated, when the ship is in port at a Class A or Class B starport.

        `<search_term>` can be a single word, or a phrase. If there is an unambiguous partial match with an entry in the database, the Library Data for that entry will be returned. If there are multiple matching terms, a list of possible matches will be returned (try again with a more specific term from the list).
        """
        for arg in args:
            search_term = f"{search_term} {arg}"
        await self.send(ctx, self.library.search(search_term))

    @commands.command(name="save")
    async def save_session_data(self, ctx, filename: str = "session_data"):
        """Save session data to a file in JSON format."""

        enc_data = jsonpickle.encode(self.session_data)
        p = f"/save/{filename}.json"
        with open(p, "w") as f:
            json.dump(json.loads(enc_data), f, indent=2)

        ts = time.gmtime()
        timestamp = time.strftime("%Y%m%d%H%M%S", ts)
        p_backup = f"/save/{filename}_{timestamp}.json"
        with open(p_backup, "w") as f:
            json.dump(json.loads(enc_data), f, indent=2)

        await self.send(ctx, f"Session data saved as: {basename(p)}. Backup in: {basename(p_backup)}")

    @commands.command(name="load")
    async def load_session_data(self, ctx, filename: str = "session_data.json"):
        """Load session data from a JSON-formatted file."""

        with open(f"../../save/{basename(filename)}", "r") as f:
            enc_data = json.dumps(json.load(f))
            self.session_data = jsonpickle.decode(enc_data)

        await self.send(ctx, f"Session data loaded from {filename}.")

    @commands.command(name="set_spaceship", aliases=["add_spaceship", "add_starship", "add_ship"])
    async def set_spaceship(
        self,
        ctx,
        name,
        size,
        capacity,
        type,
        TL,
        armour,
        containers,
        m_drive,
        j_drive,
        power_plant,
        fuel_refiner_speed,
        is_streamlined,
        has_fuel_scoop,
        has_cargo_crane,
    ):
        """Add a ship"""

        if name in self.session_data.fleet():
            raise InvalidArgument(
                f"A ship with that name: {name} already exists! If you really want to replace it, delete it first"
            )

        s = BbwSpaceShip(
            name=name,
            size=size,
            capacity=capacity,
            type=type,
            TL=TL,
            armour=armour,
            containers=eval(containers),
            m_drive=m_drive,
            j_drive=j_drive,
            power_plant=power_plant,
            fuel_refiner_speed=fuel_refiner_speed,
            is_streamlined=is_streamlined,
            has_fuel_scoop=has_fuel_scoop,
            has_cargo_crane=has_cargo_crane,
        )
        self.session_data.fleet().set_item(s)

        await self.send(ctx, f"The ship {name} was successfully added to the fleet.")
        await self.set_ship_curr(ctx, name)

    @commands.command(name="del_ship", aliases=[])
    async def del_ship(self, ctx, name):
        """Del ship"""

        self.session_data.fleet().del_item(k=name)

        await self.send(ctx, f"The ship {name} was successfully deleted.")
        await self.fleet(ctx)

    @commands.command(name="rename_ship_curr", aliases=["rename_ship"])
    async def rename_ship(self, ctx, new_name):
        cs = self.session_data.get_ship_curr()
        self.session_data.fleet().rename_item(cs, new_name)

        await self.set_ship_curr(ctx, new_name)

    @commands.command(name="ship_curr", aliases=["ship"])
    async def ship_curr(self, ctx):
        """Current ship summary"""

        cs = self.session_data.get_ship_curr()

        await self.send(ctx, cs.__str__(is_compact=False))

    @commands.command(name="set_ship_curr", aliases=[])
    async def set_ship_curr(self, ctx, name):
        """Set current ship"""

        self.session_data.set_ship_curr(name)

        await self.ship_curr(ctx)

    @commands.command(name="fleet", aliases=["ships"])
    async def fleet(self, ctx):
        """Fleet summary"""

        await self.send(ctx, self.session_data.fleet().__str__(is_compact=False))

    @commands.command(name="wish", aliases=["wishes", "wishlist"])
    async def wishlist(self, ctx):
        await self.send(ctx, self.session_data.wishlist().__str__(is_compact=False))

    @commands.command(name="add_wish", aliases=[])
    async def add_wish(self, ctx, name, count=1, TL=0, value=0):
        new_item = BbwItem(name=name, count=count, capacity=1.0, value=value, TL=TL)
        self.session_data.wishlist().add_item(new_item)

        await self.wishlist(ctx)

    @commands.command(name="del_wish", aliases=[])
    async def del_wish(self, ctx, name, count=1):
        _, item = self.session_data.wishlist().get_item(name)
        self.session_data.wishlist().del_item(item.name(), count)

        await self.wishlist(ctx)

    @commands.command(name="rename_wish", aliases=[])
    async def rename_wish(self, ctx, name, new_name):
        self.session_data.wishlist().rename_item(name, new_name)

        await self.wishlist(ctx)

    @commands.command(name="add_debt", aliases=[])
    async def add_debt(self, ctx, name, capacity, due_day, due_year, period=None, end_day=None, end_year=None):
        new_debt = BbwDebt(
            name=name,
            count=1,
            due_t=BbwCalendar.date2t(due_day, due_year),
            period=period,
            end_t=BbwCalendar.date2t(end_day, end_year),
            capacity=capacity,
        )
        self.session_data.company().debts().add_item(new_debt)

        await self.money(ctx)

    @commands.command(name="del_debt", aliases=[])
    async def del_debt(self, ctx, name, count=1):
        _, debt = self.session_data.company().debts().get_item(name)
        self.session_data.company().debts().del_item(debt.name(), count)

        await self.money(ctx)

    @commands.command(name="rename_debt", aliases=[])
    async def rename_debt(self, ctx, name, new_name):
        self.session_data.company().rename_item(name, new_name)

        await self.money(ctx)

    @commands.command(name="pay_debt", aliases=["pay_debts"])
    async def pay_debts(self, ctx, name=None):
        self.session_data.company().pay_debts(self.session_data.calendar().t(), name)

        await self.money(ctx)

    @commands.command(name="add_money", aliases=["cr"])
    async def add_money(self, ctx, value=0, description=""):
        if value:
            self.session_data.company().add_log_entry(value, description, self.session_data.calendar().t())

        await self.money(ctx, 10)

    @commands.command(name="money_status", aliases=["status", "money", "log"])
    async def money(self, ctx, log_lines=10):
        await self.send(ctx, self.session_data.company().__str__(log_lines))

    @commands.command(name="date", aliases=[])
    async def date(self, ctx):
        await self.send(ctx, self.session_data.calendar().__str__(is_compact=False))

    @commands.command(name="set_date", aliases=[])
    async def set_date(self, ctx, day, year):
        self.session_data.calendar().set_date(day, year)
        await self.send(ctx, "Date set successfully")
        await self.date(ctx)

    @commands.command(name="newday", aliases=["advance"])
    async def newday(self, ctx, ndays=1):
        n_months = self.session_data.calendar().add_t(ndays)
        for i in range(n_months):
            await self.close_month(ctx)
        await self.send(ctx, f"Date advanced by {ndays}d")
        await self.date(ctx)

    @commands.command(name="set_ship_attr", aliases=["set_ship_curr_attr"])
    async def set_ship_attr(self, ctx, attr_name, value):
        cs = self.session_data.get_ship_curr()
        cs.set_attr(attr_name, value)

        await self.ship_curr(ctx)

    @commands.command(name="set_debt_attr", aliases=[])
    async def set_debt_attr(self, ctx, debt_name, attr_name, value):
        _, debt = self.session_data.company().debts().get_item(debt_name)
        debt.set_attr(attr_name, value)

        await self.money(ctx)

    @commands.command(name="set_wish_attr", aliases=[])
    async def set_wish_attr(self, ctx, item_name, attr_name, value):
        _, item = self.session_data.wishlist().get_item(item_name)
        item.set_attr(attr_name, value)

        await self.wishlist(ctx)

    @commands.command(name="container", aliases=[])
    async def container(self, ctx, container_name):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)
        await self.send(ctx, container.__str__(False))

    @commands.command(name="cargo", aliases=[])
    async def cargo(self, ctx):
        cs = self.session_data.get_ship_curr()
        container = cs.get_main_cargo()
        await self.send(ctx, container.__str__(False))

    @commands.command(name="stateroom", aliases=[])
    async def stateroom(self, ctx):
        cs = self.session_data.get_ship_curr()
        container = cs.get_main_stateroom()
        await self.send(ctx, container.__str__(False))

    @commands.command(name="add_person", aliases=[])
    async def add_person(
        self,
        ctx,
        container_name,
        name,
        role,
        salary_ticket=None,
        capacity=None,
        upp=None,
        reinvest=False,
        count=1,
    ):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        new_person = BbwPerson(
            name=name,
            count=count,
            role=role,
            salary_ticket=salary_ticket,
            capacity=capacity,
            reinvest=reinvest,
            upp=upp,
        )
        container.add_item(new_person)

        await self.container(ctx, container.name())

    @commands.command(name="move", aliases=[])
    async def move(self, ctx, name, to0, from0=None):
        """add item to container"""
        cs = self.session_data.get_ship_curr()
        container_to0 = cs.get_container(to0)
        if from0 is None:
            container_from0 = cs.get_main_cargo()
        else:
            container_from0 = cs.get_container(from0)

        _, item = container_from0.get_item(name)
        container_to0.add_item(item)
        container_from0.del_item(item.name(), item.count())

        await self.send(ctx, f"{item.name()} moved from {container_from0.name()} to {container_to0.name()}")

    @commands.command(name="buy", aliases=[])
    async def buy(self, ctx, container_name, name, value=0, count=1, capacity=0, TL=0, size=None, price_payed=None):
        """add item to container"""
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        new_item = BbwItem(name=name, count=count, capacity=capacity, TL=TL, value=value, size=size)
        container.add_item(new_item)

        self.session_data.company().add_log_entry(
            -new_item.value() if price_payed is None else -price_payed,
            f"{new_item.name()} ({new_item.count()})",
            self.session_data.calendar().t(),
        )

        await self.send(ctx, new_item.__str__(False))

    @commands.command(name="sell", aliases=[])
    async def sell(self, ctx, container_name, name, count=1, price_payed=None):
        """add item to container"""
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        name, item = container.get_item(name)

        old_count = item.count()
        if price_payed is None:
            item.set_count(count)
            price_payed = item.value()
            item.set_count(old_count)

        self.session_data.company().add_log_entry(
            price_payed, f"{item.name()} ({count})", self.session_data.calendar().t()
        )

        container.del_item(name, count)

        await self.send(ctx, f"{name} ({count}) was sold for: {price_payed} Cr. Remaining count: {old_count-count}")

    @commands.command(name="add_item", aliases=[])
    async def add_item(self, ctx, container_name, name, count=1, capacity=0.0, TL=0, value=0, size=None):
        """add item to container"""
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        new_item = BbwItem(name=name, count=count, capacity=capacity, TL=TL, value=value, size=size)
        container.add_item(new_item)

        await self.container(ctx, container.name())

    @commands.command(name="del_person", aliases=["del_item", "del"])
    async def del_item(self, ctx, container_name, name, count=1):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        _, item = container.get_item(name)
        container.del_item(item.name(), count)

        await self.container(ctx, container.name())

    @commands.command(name="rename_person", aliases=["rename_item", "rename"])
    async def rename_item(self, ctx, container_name, name, new_name):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        container.rename_item(name, new_name)

        await self.container(ctx, container.name())

    @commands.command(name="set_person_attr", aliases=["set_item_attr"])
    async def set_item_attr(self, ctx, container_name, item_name, attr_name, value):
        cs = self.session_data.get_ship_curr()
        container = cs.get_container(container_name)

        _, item = container.get_item(item_name)

        item.set_attr(attr_name, value)

        await self.container(ctx, container.name())

    @commands.command(name="pay_salaries", aliases=[])
    async def pay_salaries(self, ctx, print_recap=True):
        cs = self.session_data.get_ship_curr()
        self.session_data.company().pay_salaries(cs.get_crew(), self.session_data.calendar().t())

        if print_recap:
            await self.money(ctx, 10)

    @commands.command(name="flight_time_m_drive", aliases=["m_drive_t", "m_drive"])
    async def flight_time_m_drive(self, ctx, d_km):
        cs = self.session_data.get_ship_curr()

        t = conv_days_2_time(cs.flight_time_m_drive(d_km))

        await self.send(ctx, f"the m drive {cs.m_drive()} travel time to cover {d_km} km is: {t}")

    @commands.command(name="flight_time_j_drive", aliases=["j_drive_t", "j_drive"])
    async def flight_time_j_drive(self, ctx, n_jumps=1):
        cs = self.session_data.get_ship_curr()

        t = conv_days_2_time(cs.flight_time_j_drive(n_jumps))

        await self.send(ctx, f"the j drive {cs.j_drive()} travel time to do {n_jumps} jumps is: {t}")

    @commands.command(name="trip_accounting_life_support", aliases=[])
    async def trip_accounting_life_support(self, ctx, t):
        cs = self.session_data.get_ship_curr()
        life_support_costs = cs.var_life_support(t)
        self.session_data.company().add_log_entry(
            -life_support_costs, f"variable life support", self.session_data.calendar().t()
        )

        await self.send(ctx, f"variable life support costs: {life_support_costs} Cr")

    @commands.command(name="trip_accounting_payback", aliases=[])
    async def trip_accounting_payback(self, ctx, t):
        cs = self.session_data.get_ship_curr()

        msg = f""
        crew = cs.get_crew()
        for i in crew:
            payback = i.trip_payback(t)

            if payback is None:
                msg += f"I do not know {i.name()} upp. I cannot calculate his/her/their payback!\n"
            else:
                if i.reinvest():
                    self.session_data.company().add_log_entry(
                        payback, f"{i.name()} reinvested the payback", self.session_data.calendar().t()
                    )
                msg += f"{i.name()} gets back {payback} Cr {'(reinvested)' if i.reinvest() else ''}\n"

        await self.send(ctx, msg)

    @commands.command(name="find_passengers", aliases=[])
    async def find_passengers(self, ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, w_to_name):
        cs = self.session_data.get_ship_curr()
        w0 = self.session_data.get_world_curr()
        _, w1 = self.session_data.charted_space().get_item(w_to_name)

        header = ("high", "middle", "basic", "low")
        np = [cs.find_passengers(carouse_or_broker_or_streetwise_mod, SOC_mod, i, w0, w1) for i in header]

        await self.send(ctx, f"passengers:\n{print_table(np, headers=header)}")

    @commands.command(name="find_mail_and_freight", aliases=[])
    async def find_mail_and_freight(self, ctx, brocker_or_streetwise_mod, SOC_mod, w_to_name):
        cs = self.session_data.get_ship_curr()
        w0 = self.session_data.get_world_curr()
        _, w1 = self.session_data.charted_space().get_item(w_to_name)

        header = ("mail", "major", "minor", "incidental")
        mail, mail_money = cs.find_mail(brocker_or_streetwise_mod, SOC_mod, w0, w1)
        np = [mail, *[cs.find_freight(brocker_or_streetwise_mod, SOC_mod, i, w0, w1) for i in header[1:]]]

        if mail_money:
            self.session_data.company().add_log_entry(mail_money, f"mail", self.session_data.calendar().t())

        await self.send(ctx, f"mail and freight:\n{print_table(np, headers=header)}")

    @commands.command(name="unload_passengers", aliases=[])
    async def unload_passengers(self, ctx, except_set="set()"):
        cs = self.session_data.get_ship_curr()
        except_set = eval(except_set)
        except_dict = {i: 0 for i in except_set}

        passengers = cs.get_passengers()
        tot = 0
        for p in passengers:
            tot += p.salary_ticket()
            try:
                _, _ = get_item(p.name(), except_dict)
            except SelectionException:
                if p.luggage() > 0:
                    cargo = cs.get_main_cargo()
                    cargo.del_item(p.name())
                container = cs.get_main_stateroom() if "low" not in p.name() else cs.get_main_lowberth()
                container.del_item(p.name(), c=p.count())

        self.session_data.company().add_log_entry(tot, f"passenger tickets", self.session_data.calendar().t())

        await self.send(ctx, f"passenger tickets: {int(tot)} Cr")

    @commands.command(name="unload_mail_and_freight", aliases=[])
    async def unload_mail_and_freight(self, ctx):
        cs = self.session_data.get_ship_curr()

        tot = 0
        for container in cs.get_all_cargo_containers():
            freight_items = [i for i in container.values() if "freight" in i.name()]
            for item in freight_items:
                tot += item.value()
                container.del_item(item.name(), c=item.count())

            mail_items = [i for i in container.values() if "mail" in i.name()]
            for item in mail_items:
                container.del_item(item.name(), c=item.count())
        self.session_data.company().add_log_entry(tot, f"freight", self.session_data.calendar().t())

        await self.send(ctx, f"freight: {int(tot)} Cr")

    @commands.command(name="unload_ship", aliases=[])
    async def unload(self, ctx, except_set="{}"):
        await self.unload_passengers(ctx, except_set)
        await self.unload_mail_and_freight(ctx)


    @commands.command(name="fuel", aliases=[])
    async def fuel(self, ctx, source, q=1000):
        if q > 0:
            await self.add_fuel(ctx, q)
        else:
            await self.consume_fuel(ctx, q)
    @commands.command(name="get_fuel", aliases=["add_fuel", "refuel"])
    async def add_fuel(self, ctx, source, q=1000):
        cs = self.session_data.get_ship_curr()
        q, price, t = cs.add_fuel(source, q)

        if price != 0:
            self.session_data.company().add_log_entry(
                -price, f"{source} fuel ({q} tons)", self.session_data.calendar().t()
            )

        await self.send(ctx, f"{q} tons of fuel added for {price} Cr and {conv_days_2_time(t)}")

    @commands.command(name="consume_fuel", aliases=[])
    async def consume_fuel(self, ctx, q):
        cs = self.session_data.get_ship_curr()
        cs.consume_fuel(q)

        await self.send(ctx, f"{q} tons of fuel consumed\n{cs.get_fuel_tank().__str__(False)}")

    @commands.command(name="refine_fuel", aliases=[])
    async def refine_fuel(self, ctx):
        cs = self.session_data.get_ship_curr()
        q, t = cs.refine_fuel()

        await self.send(ctx, f"{q} tons of fuel refined in: {conv_days_2_time(t)}")

        t = math.floor(t)
        if t > 0:
            await self.newday(ctx, ndays=math.floor(t))

    @commands.command(name="close_month", aliases=[])
    async def close_month(self, ctx):
        await self.consume_fuel(ctx, 1)
        await self.pay_salaries(ctx, False)
        await self.pay_debts(ctx)

    @commands.command(name="jump_time", aliases=["p2p", "w2w"])
    async def jump_time_world_2_world(self, ctx, w_to_name, w_from_name=None):
        cs = self.session_data.get_ship_curr()
        _, w1 = self.session_data.charted_space().get_item(w_to_name)
        if w_from_name == None:
            w0 = self.session_data.get_world_curr()
        else:
            _, w0 = self.session_data.charted_space().get_item(w_from_name)

        t1, t2, t3, n_sectors, n_jumps = cs.jump_time_world_2_world(w0, w1)

        tab = [
            [f"m drive ({round(100 * float(w0.d_km()))} km)", conv_days_2_time(t1)],
            [f"j drive ({n_jumps} jumps)", conv_days_2_time(t2)],
            [f"m drive ({round(100 * float(w1.d_km()))} km)", conv_days_2_time(t3)],
        ]

        await self.send(
            ctx, f"the total travel time is:\n{print_table(tab)}\n= {conv_days_2_time(t1+t2+t3)} ({n_sectors} sectors)"
        )

        return (t1 + t2 + t3, n_sectors)

    @commands.command(name="jump", aliases=[])
    async def jump(self, ctx, w_to_name):
        """all the operations necessary to jump from current world to w_to_name world"""

        # jump time
        t, n_sectors = await self.jump_time_world_2_world(ctx, w_to_name)

        # life support
        await self.trip_accounting_life_support(ctx, t)

        # payback
        await self.trip_accounting_payback(ctx, t)

        await self.consume_fuel(ctx, 20 * n_sectors)

        t = math.floor(t)
        if t > 0:
            await self.newday(ctx, t)

        await self.set_world_curr(ctx, w_to_name)

    @commands.command(name="load_ship", aliases=[])
    async def load_ship(self, ctx, carouse_or_broker_or_streetwise_mod, brocker_or_streetwise_mod, SOC_mod, w_to_name):
        # load passengers
        await self.find_passengers(ctx, carouse_or_broker_or_streetwise_mod, SOC_mod, w_to_name)

        # load mail and freight
        await self.find_mail_and_freight(
            ctx,
            brocker_or_streetwise_mod,
            SOC_mod,
            w_to_name,
        )

    @commands.command(name="set_world", aliases=["add_world", "set_planet", "add_planet"])
    async def set_world(self, ctx, name, uwp, zone, hex):
        """Add a world"""

        if name in self.session_data.charted_space():
            raise InvalidArgument(
                f"A ship with that name: {name} already exists! If you really want to replace it, delete it first"
            )

        w = BbwWorld(name=name, uwp=uwp, zone=zone, hex=hex)
        self.session_data.charted_space().set_item(w)

        await self.send(ctx, f"The world {name} was successfully added to the charted space")

    @commands.command(name="del_world", aliases=["del_planet"])
    async def del_world(self, ctx, name):
        """Del world"""

        self.session_data.charted_space().del_item(k=name)

        await self.send(ctx, f"The world {name} was successfully deleted")
        await self.charted_space(ctx)

    @commands.command(name="rename_world_curr", aliases=["rename_world", "rename_planet"])
    async def rename_world(self, ctx, new_name):
        cs = self.session_data.get_world_curr()
        self.session_data.fleet().rename_item(cs, new_name)

        await self.set_world_curr(ctx, new_name)

    @commands.command(name="world_curr", aliases=["world", "planet"])
    async def world_curr(self, ctx):
        """Current world summary"""

        cs = self.session_data.get_world_curr()

        await self.send(ctx, f"current world:\n{cs.__str__(is_compact=False)}")

    @commands.command(name="set_world_curr", aliases=["set_planet_curr"])
    async def set_world_curr(self, ctx, name):
        """Set current world"""

        self.session_data.set_world_curr(name)

        await self.world_curr(ctx)

    @commands.command(name="charted_space", aliases=["galaxy"])
    async def charted_space(self, ctx):
        """charted space summary"""

        await self.send(ctx, self.session_data.charted_space().__str__(is_compact=False))

    @commands.command(name="set_world_attr", aliases=["set_world_curr_attr", "set_planet_curr_attr"])
    async def set_world_attr(self, ctx, attr_name, value):
        cw = self.session_data.get_world_curr()
        cw.set_attr(attr_name, value)

        await self.world_curr(ctx)
