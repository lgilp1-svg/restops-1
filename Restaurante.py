import tkinter as tk
import re
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("light")

# ---------- Colores y constantes ----------
P, P2, INK = "#6c4ff6", "#18c5b5", "#1b1740"
BG, LINE, MUTED = "#f3f2fb", "#e3e1f2", "#6f6c8f"
RED, RED_BG = "#e5484d", "#fdeced"
OK, OK_BG = "#0f9f8f", "#dff7f3"
AMB, AMB_BG = "#b7791f", "#fff4dc"
CAPACIDAD, LIMITE = 50, 0.8
BADGE = {"Alta": (RED_BG, RED), "Media": (AMB_BG, AMB), "Baja": (OK_BG, OK),
         "Confirmada": (OK_BG, OK), "Pendiente": (AMB_BG, AMB), "Completada": (OK_BG, OK), "Cancelada": ("#eceaf5", MUTED)}
EMPLEADOS = [("Juan M.", "Mesero"), ("Laura R.", "Cocina"), ("Pedro S.", "Barra"), ("Sofía T.", "Mesera")]
MENU = [("📅", "Reservas"), ("📊", "Panel de Ocupación"), ("📝", "Asignación de Tareas"), ("✅", "Mis Tareas"), ("🚚", "Proveedores")]


# ---------- Ayudas de diseño ----------
def f(size=14, bold=False, **kw):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold" if bold else "normal", **kw)

def card(parent):
    return ctk.CTkFrame(parent, fg_color="white", corner_radius=14, border_width=1, border_color=LINE)

def boton(parent, texto, cmd, ghost=False):
    return ctk.CTkButton(parent, text=texto, command=cmd, height=38, corner_radius=10, font=f(14, True),
                         fg_color="transparent" if ghost else P,
                         hover_color="#ece9ff" if ghost else "#5538d6",
                         text_color=INK if ghost else "white",
                         border_width=1 if ghost else 0, border_color=LINE)

def etiqueta(parent, texto):
    ctk.CTkLabel(parent, text=texto, font=f(13, True), text_color=INK).pack(anchor="w", pady=(12, 4))

def campo(parent, texto, placeholder=""):
    etiqueta(parent, texto)
    e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=38, border_color=LINE,
                     fg_color="white", text_color=INK)
    e.pack(fill="x")
    return e

def lista(parent, texto, valores):
    etiqueta(parent, texto)
    o = ctk.CTkOptionMenu(parent, values=valores, height=38, fg_color="white", text_color=INK,
                          button_color=P, button_hover_color="#5538d6", dropdown_fg_color="white",
                          dropdown_text_color=INK, dropdown_hover_color="#ece9ff")
    o.pack(fill="x")
    return o

def badge(parent, texto):
    fg, tc = BADGE[texto]
    return ctk.CTkLabel(parent, text=texto, fg_color=fg, text_color=tc, corner_radius=10,
                        font=f(12, True), width=84, height=24)

def msg_label(parent):
    return ctk.CTkLabel(parent, text="", corner_radius=8, font=f(13, True), wraplength=360,
                        justify="left", anchor="w")

def mensaje(lbl, texto="", ok=False):
    if not texto:
        lbl.configure(text="", fg_color="transparent")
        return
    lbl.configure(text="  " + texto, fg_color=OK_BG if ok else RED_BG, text_color=OK if ok else RED)


# ---------- Aplicación ----------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RestOps – Gestión de restaurante")
        self.geometry("1120x720")
        self.minsize(980, 640)
        self.configure(fg_color=BG)

        # Datos simulados
        self.reservas = [
            {"hora": "12:30", "cliente": "Ana P.", "pers": 2, "mesa": "Mesa 2", "estado": "Confirmada"},
            {"hora": "13:00", "cliente": "Familia Ruiz", "pers": 6, "mesa": "Mesa 8", "estado": "Confirmada"},
            {"hora": "14:15", "cliente": "Luis G.", "pers": 3, "mesa": "Mesa 3", "estado": "Pendiente"},
            {"hora": "20:00", "cliente": "Marta S.", "pers": 4, "mesa": "Mesa 6", "estado": "Confirmada"},
        ]
        from datetime import date, timedelta
        self.hoy = date.today().isoformat()
        self.manana = (date.today() + timedelta(days=1)).isoformat()
        for r in self.reservas:
            r["sede"], r["fecha"] = "Centro", self.hoy
        self.reservas += [
            {"hora": "13:30", "cliente": "Pablo R.", "pers": 5, "mesa": "Mesa 1", "estado": "Confirmada", "sede": "Norte", "fecha": self.hoy},
            {"hora": "19:30", "cliente": "Elena V.", "pers": 8, "mesa": "Mesa 4", "estado": "Pendiente", "sede": "Centro", "fecha": self.manana}]
        self.sede, self.fecha = "Centro", self.hoy
        self.tareas = {"Juan M.": [("Armar las mesas de la terraza", "Media")],
                       "Laura R.": [("Preparar mise en place", "Alta")], "Pedro S.": [], "Sofía T.": []}
        self.mis = [{"t": "Limpiar la zona de barra", "p": "Media", "ok": False},
                    {"t": "Revisar inventario de bebidas", "p": "Alta", "ok": False},
                    {"t": "Reponer servilletas", "p": "Baja", "ok": True}]
        self.filtro, self.emp_sel, self.menu_abierto = None, "Juan M.", False
        self.views, self.nav_btns = {}, {}

        self.crear_topbar()
        self.cont = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.cont.pack(fill="both", expand=True)
        self.cont.bind("<Button-1>", lambda e: self.cerrar_menu())
        self.bind("<Escape>", lambda e: self.cerrar_menu())

        self.build_reservas()
        self.build_asignar()
        self.build_mis()
        self.build_proveedores()
        self.build_panel()
        self.crear_drawer()
        self.mostrar("Reservas")

    # ----- Barra superior y menú derecho -----
    def crear_topbar(self):
        top = ctk.CTkFrame(self, height=62, fg_color="#2d2380", corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkButton(top, text="☰  Menú", width=110, height=36, corner_radius=10, font=f(14, True),
                      fg_color="#4a3bc0", hover_color="#5d4de0", command=self.alternar_menu
                      ).pack(side="left", padx=(24, 12))
        logo = ctk.CTkLabel(top, text=" M ", fg_color=P2, text_color="#10243a", corner_radius=8, font=f(18, True))
        logo.pack(side="left", padx=(0, 8))
        nombre = ctk.CTkLabel(top, text="RestOps", text_color="white", font=f(18, True))
        nombre.pack(side="left")
        for w in (logo, nombre):
            w.bind("<Button-1>", lambda e: self.mostrar("Reservas"))
        self.titulo = ctk.CTkLabel(top, text="Reservas", text_color="#cfc8ff", font=f(15))
        self.titulo.pack(side="left", padx=24)

    def crear_drawer(self):
        d = self.drawer = ctk.CTkFrame(self, width=280, fg_color=INK, corner_radius=0)
        d.pack_propagate(False)
        fila = ctk.CTkFrame(d, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=(20, 18))
        ctk.CTkLabel(fila, text="GR", width=40, height=40, corner_radius=20, fg_color=P,
                     text_color="white", font=f(14, True)).pack(side="left")
        ctk.CTkLabel(fila, text="Gerente\nSucursal Centro", justify="left", text_color="white",
                     font=f(13, True)).pack(side="left", padx=10)
        ctk.CTkButton(fila, text="✕", width=30, height=30, fg_color="transparent", hover_color="#2d2a66",
                      command=self.cerrar_menu).pack(side="right")
        for icono, nombre in MENU:
            b = ctk.CTkButton(d, text=f"{icono}   {nombre}", anchor="w", height=44, corner_radius=10,
                              font=f(14), fg_color="transparent", hover_color="#2d2a66",
                              text_color="#d9d4ff", command=lambda n=nombre: self.mostrar(n))
            b.pack(fill="x", padx=14, pady=3)
            self.nav_btns[nombre] = b

    def mover_drawer(self, x, destino, fin=None):
        self.drawer.place(relx=0.0, x=x, rely=0, anchor="nw", relheight=1)
        if x == destino:
            if fin:
                fin()
            return
        sig = min(x + 40, destino) if destino > x else max(x - 40, destino)
        self.after(12, lambda: self.mover_drawer(sig, destino, fin))

    def abrir_menu(self):
        if not self.menu_abierto:
            self.menu_abierto = True
            self.drawer.lift()
            self.mover_drawer(-280, 0)

    def cerrar_menu(self):
        if self.menu_abierto:
            self.menu_abierto = False
            self.mover_drawer(0, -280, self.drawer.place_forget)

    def alternar_menu(self):
        self.cerrar_menu() if self.menu_abierto else self.abrir_menu()

    def mostrar(self, nombre):
        for v in self.views.values():
            v.pack_forget()
        self.views[nombre].pack(fill="both", expand=True, padx=28, pady=20)
        self.titulo.configure(text=nombre)
        for n, b in self.nav_btns.items():
            b.configure(fg_color=P if n == nombre else "transparent",
                        text_color="white" if n == nombre else "#d9d4ff")
        if nombre == "Panel de Ocupación":
            self.after(50, self.pintar_panel)
        self.cerrar_menu()

    def toast(self, texto):
        t = ctk.CTkLabel(self, text="  " + texto + "  ", fg_color=INK, text_color="white",
                         corner_radius=10, height=40, font=f(14, True))
        t.place(x=24, rely=1.0, y=-24, anchor="sw")
        self.after(2200, t.destroy)

    # ----- 1. RESERVAS -----
    def build_reservas(self):
        v = self.views["Reservas"] = ctk.CTkFrame(self.cont, fg_color=BG)
        stats = ctk.CTkFrame(v, fg_color=BG)
        stats.pack(fill="x")
        self.st = {}
        for i, (k, color) in enumerate([("Reservas hoy", P), ("Personas", P2), ("Pendientes", "#f5a524")]):
            stats.columnconfigure(i, weight=1)
            c = card(stats)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0 if i == 2 else 8))
            ctk.CTkFrame(c, width=5, fg_color=color, corner_radius=3).pack(side="left", fill="y", padx=(10, 0), pady=10)
            box = ctk.CTkFrame(c, fg_color="transparent")
            box.pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(box, text=k, text_color=MUTED, font=f(13)).pack(anchor="w")
            self.st[k] = ctk.CTkLabel(box, text="0", text_color=INK, font=f(28, True))
            self.st[k].pack(anchor="w")
        flt = ctk.CTkFrame(v, fg_color=BG)
        flt.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(flt, text="Sede", font=f(13, True), text_color=INK).pack(side="left")
        self.o_sede = ctk.CTkOptionMenu(flt, values=["Centro", "Norte", "Sur"], width=120, fg_color="white",
                                        text_color=INK, button_color=P, dropdown_fg_color="white",
                                        dropdown_text_color=INK, command=self.cambiar_filtro)
        self.o_sede.pack(side="left", padx=(8, 20))
        ctk.CTkLabel(flt, text="Fecha (AAAA-MM-DD)", font=f(13, True), text_color=INK).pack(side="left")
        self.e_fecha = ctk.CTkEntry(flt, width=130, height=32, border_color=LINE, fg_color="white", text_color=INK)
        self.e_fecha.insert(0, self.hoy)
        self.e_fecha.pack(side="left", padx=8)
        self.e_fecha.bind("<Return>", lambda e: self.cambiar_filtro())
        boton(flt, "Buscar", self.cambiar_filtro).pack(side="left")

        barra = ctk.CTkFrame(v, fg_color=BG)
        barra.pack(fill="x", pady=12)
        self.chips = {}
        for texto, valor in [("Todas", None), ("Confirmadas", "Confirmada"), ("Pendientes", "Pendiente")]:
            b = ctk.CTkButton(barra, text=texto, width=110, height=34, corner_radius=17, font=f(13),
                              command=lambda t=texto, val=valor: self.set_filtro(t, val))
            b.pack(side="left", padx=(0, 8))
            self.chips[texto] = b
        boton(barra, "+ Nueva Reserva", self.abrir_modal).pack(side="right")

        tc = card(v)
        tc.pack(fill="both", expand=True)
        self.tabla = ctk.CTkScrollableFrame(tc, fg_color="transparent")
        self.tabla.pack(fill="both", expand=True, padx=8, pady=8)
        for i in range(6):
            self.tabla.columnconfigure(i, weight=1, uniform="c")

        ac = card(v)
        ac.pack(fill="x", pady=(12, 0))
        cab = ctk.CTkFrame(ac, fg_color="transparent")
        cab.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(cab, text="Aforo del restaurante", font=f(14, True), text_color=INK).pack(side="left")
        self.cap_txt = ctk.CTkLabel(cab, text="", font=f(13), text_color=INK)
        self.cap_txt.pack(side="right")
        wrap = ctk.CTkFrame(ac, fg_color="transparent")
        wrap.pack(fill="x", padx=16)
        self.cap_bar = ctk.CTkProgressBar(wrap, height=16, corner_radius=8, fg_color=LINE, progress_color=P)
        self.cap_bar.pack(fill="x")
        ctk.CTkFrame(wrap, width=3, height=16, fg_color=RED, corner_radius=0).place(relx=0.8, y=0)
        ctk.CTkLabel(ac, text="Límite para reservas: 80% (40 personas). La línea roja marca el tope.",
                     text_color=MUTED, font=f(12)).pack(anchor="w", padx=16, pady=(6, 12))

    def set_filtro(self, texto, valor):
        self.filtro = valor
        self.pintar_reservas()

    def visibles(self):
        return [r for r in self.reservas if r["sede"] == self.sede and r["fecha"] == self.fecha]

    def total_personas(self):
        return sum(r["pers"] for r in self.visibles() if r["estado"] != "Cancelada")

    def cambiar_filtro(self, *_):
        fecha = self.e_fecha.get().strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
            self.fecha = fecha
        self.sede = self.o_sede.get()
        self.pintar_reservas()

    def confirmar_cancelar(self, r):
        if messagebox.askyesno("RestOps", f"¿Cancelar la reserva de {r['cliente']}?"):
            r["estado"] = "Cancelada"
            self.after(10, self.pintar_reservas)
            self.toast(f"Reserva de {r['cliente']} cancelada")

    def alerta_aforo(self):
        self.cap_bar.set(1)
        self.cap_bar.configure(progress_color=RED)
        self.cap_txt.configure(text="⚠ Aforo máximo superado", text_color=RED)
        self.after(4000, lambda: (self.cap_txt.configure(text_color=INK), self.pintar_reservas()))

    def cambiar_estado(self, reserva, nuevo):
        reserva["estado"] = nuevo
        self.after(10, self.pintar_reservas)
        self.toast(f"Reserva de {reserva['cliente']}: {nuevo}")

    def pintar_reservas(self):
        for w in self.tabla.winfo_children():
            w.destroy()
        for i, h in enumerate(["Hora", "Cliente", "Personas", "Mesa", "Estado", "Acción"]):
            ctk.CTkLabel(self.tabla, text=h, text_color=MUTED, font=f(13, True), anchor="w"
                         ).grid(row=0, column=i, sticky="w", padx=8, pady=(2, 8))
        datos = sorted([r for r in self.visibles() if self.filtro in (None, r["estado"])], key=lambda r: r["hora"])
        if not datos:
            ctk.CTkLabel(self.tabla, text="No hay reservas para esta sede y fecha.", text_color=MUTED
                         ).grid(row=1, column=0, columnspan=6, pady=16)
        for n, r in enumerate(datos, start=1):
            for i, val in enumerate([r["hora"], r["cliente"], r["pers"], r["mesa"]]):
                ctk.CTkLabel(self.tabla, text=str(val), text_color=INK, anchor="w",
                             font=f(14, i == 0)).grid(row=n, column=i, sticky="w", padx=8, pady=7)
            fg, tc = BADGE[r["estado"]]
            om = ctk.CTkOptionMenu(self.tabla, values=["Confirmada", "Pendiente", "Cancelada"],
                                   width=130, height=28, font=f(12, True),
                                   fg_color=fg, text_color=tc, button_color=fg, button_hover_color=fg,
                                   dropdown_fg_color="white", dropdown_text_color=INK,
                                   dropdown_hover_color="#ece9ff",
                                   command=lambda nuevo, r=r: self.cambiar_estado(r, nuevo))
            om.set(r["estado"])
            om.grid(row=n, column=4, sticky="w", padx=8)
            if r["estado"] != "Cancelada":
                ctk.CTkButton(self.tabla, text="Cancelar", width=84, height=28, corner_radius=8, font=f(12, True),
                              fg_color=RED, hover_color="#c93a3f", text_color="white",
                              command=lambda r=r: self.confirmar_cancelar(r)).grid(row=n, column=5, sticky="w", padx=8)
        for texto, b in self.chips.items():
            activo = (texto == "Todas" and self.filtro is None) or texto[:-1].rstrip("a") in (self.filtro or "") and texto != "Todas"
            b.configure(fg_color=P if activo else "#ece9ff", text_color="white" if activo else INK,
                        hover_color="#5538d6" if activo else "#ddd8ff")
        n = self.total_personas()
        pct = n / CAPACIDAD
        self.cap_txt.configure(text=f"{n} de {CAPACIDAD} personas ({round(pct * 100)}%)")
        self.cap_bar.set(min(pct, 1))
        self.cap_bar.configure(progress_color=RED if pct >= LIMITE else P)
        activas = [r for r in self.visibles() if r["estado"] != "Cancelada"]
        self.st["Reservas hoy"].configure(text=str(len(activas)))
        self.st["Personas"].configure(text=str(n))
        self.st["Pendientes"].configure(text=str(sum(r["estado"] == "Pendiente" for r in activas)))
        self.pintar_panel()

    # ----- 2. MODAL NUEVA RESERVA -----
    def abrir_modal(self):
        m = ctk.CTkToplevel(self)
        m.title("Nueva Reserva")
        m.geometry("430x650")
        m.resizable(False, False)
        m.configure(fg_color="white")
        m.transient(self)
        self.after(150, lambda: (m.lift(), m.focus_force(), m.grab_set()))

        cuerpo = ctk.CTkFrame(m, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=28, pady=22)
        ctk.CTkLabel(cuerpo, text="Nueva Reserva", font=f(20, True), text_color=INK).pack(anchor="w")
        e_nom = campo(cuerpo, "Nombre del cliente", "Ej. Carlos M.")
        o_sede = lista(cuerpo, "Sede", ["Centro", "Norte", "Sur"])
        o_sede.set(self.sede)
        e_hora = campo(cuerpo, "Hora (HH:MM)", "19:00")
        e_pers = campo(cuerpo, "Personas", "4")
        o_mesa = lista(cuerpo, "Mesa", ["Seleccionar mesa…"])
        lbl = msg_label(cuerpo)
        lbl.pack(fill="x", pady=(14, 0))

        def ocupadas_de(sede):
            return {r["mesa"] for r in self.reservas
                    if r["sede"] == sede and r["fecha"] == self.fecha and r["estado"] != "Cancelada"}

        def cargar_mesas(*_):
            oc = ocupadas_de(o_sede.get())
            o_mesa.configure(values=["Seleccionar mesa…"] + [
                f"Mesa {i}" + (" (reservada)" if f"Mesa {i}" in oc else "") for i in range(1, 11)])
            o_mesa.set("Seleccionar mesa…")

        o_sede.configure(command=cargar_mesas)
        cargar_mesas()

        def guardar():
            sede = o_sede.get()
            nombre, hora, mesa = e_nom.get().strip(), e_hora.get().strip(), o_mesa.get().split(" (")[0]
            try:
                pers = int(e_pers.get())
            except ValueError:
                pers = 0
            if not nombre or not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", hora) or pers <= 0 or mesa.startswith("Seleccionar"):
                mensaje(lbl, "Completa todos los campos: nombre, sede, hora (ej. 19:00), personas y mesa.")
                return
            en_sede = sum(r["pers"] for r in self.reservas
                          if r["sede"] == sede and r["fecha"] == self.fecha and r["estado"] != "Cancelada")
            if en_sede + pers > CAPACIDAD * LIMITE:
                mensaje(lbl, "Error: Esta reserva supera el 80% de la capacidad del restaurante")
                self.sede = sede
                self.o_sede.set(sede)
                self.pintar_reservas()
                self.alerta_aforo()
                return
            if mesa in ocupadas_de(sede):
                mensaje(lbl, "Esa mesa ya está reservada. Elige una mesa libre.")
                return
            h, mi = hora.split(":")
            self.reservas.append({"hora": f"{int(h):02d}:{mi}", "cliente": nombre, "pers": pers,
                                  "mesa": mesa, "estado": "Confirmada", "sede": sede, "fecha": self.fecha})
            self.sede = sede
            self.o_sede.set(sede)
            m.destroy()
            self.pintar_reservas()
            messagebox.showinfo("RestOps", f"Reserva guardada con éxito en la sede {sede}")

        fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila.pack(fill="x", side="bottom")
        boton(fila, "Cancelar", m.destroy, ghost=True).pack(side="left", expand=True, fill="x", padx=(0, 6))
        boton(fila, "Guardar reserva", guardar).pack(side="left", expand=True, fill="x", padx=(6, 0))

    # ----- PANEL DE OCUPACIÓN -----
    def build_panel(self):
        v = self.views["Panel de Ocupación"] = ctk.CTkFrame(self.cont, fg_color=BG)
        fila = ctk.CTkFrame(v, fg_color=BG)
        fila.pack(fill="x")
        self.pst = {}
        for i, k in enumerate(["Ocupación", "Mesas libres", "Personas esperadas"]):
            fila.columnconfigure(i, weight=1)
            c = card(fila)
            c.grid(row=0, column=i, sticky="ew", padx=6)
            ctk.CTkLabel(c, text=k, text_color=MUTED, font=f(13)).pack(anchor="w", padx=16, pady=(10, 0))
            self.pst[k] = ctk.CTkLabel(c, text="0", text_color=INK, font=f(28, True))
            self.pst[k].pack(anchor="w", padx=16, pady=(0, 10))
        gc = card(v)
        gc.pack(fill="x", pady=12)
        ctk.CTkLabel(gc, text="Ocupación por hora", font=f(16, True), text_color=INK).pack(anchor="w", padx=16, pady=(14, 0))
        self.lienzo = tk.Canvas(gc, height=210, bg="white", highlightthickness=0)
        self.lienzo.pack(fill="x", padx=16, pady=12)
        mc = card(v)
        mc.pack(fill="x")
        ctk.CTkLabel(mc, text="Estado de las mesas", font=f(16, True), text_color=INK).pack(anchor="w", padx=16, pady=(14, 4))
        self.rej = ctk.CTkFrame(mc, fg_color="transparent")
        self.rej.pack(fill="x", padx=12, pady=(0, 14))

    def pintar_panel(self):
        act = [r for r in self.visibles() if r["estado"] != "Cancelada"]
        n = sum(r["pers"] for r in act)
        ocup = {r["mesa"] for r in act}
        self.pst["Ocupación"].configure(text=f"{round(n / CAPACIDAD * 100)}%")
        self.pst["Mesas libres"].configure(text=str(10 - len(ocup)))
        self.pst["Personas esperadas"].configure(text=str(n))
        c = self.lienzo
        c.delete("all")
        w = max(c.winfo_width(), 700)
        horas = list(range(12, 23))
        por = {h: sum(r["pers"] for r in act if int(r["hora"][:2]) == h) for h in horas}
        mx = max(8, max(por.values()))
        ancho = (w - 40) / len(horas)
        for i, h in enumerate(horas):
            x0 = 20 + i * ancho + 8
            x1 = x0 + ancho - 16
            alto = por[h] / mx * 140
            c.create_rectangle(x0, 165 - alto, x1, 165, fill=P, outline="")
            if por[h]:
                c.create_text((x0 + x1) / 2, 155 - alto, text=str(por[h]), fill=INK, font=("Segoe UI", 10, "bold"))
            c.create_text((x0 + x1) / 2, 185, text=f"{h}h", fill=MUTED, font=("Segoe UI", 10))
        for w_ in self.rej.winfo_children():
            w_.destroy()
        for k in range(10):
            m = f"Mesa {k + 1}"
            oc = m in ocup
            ctk.CTkLabel(self.rej, text=f"{m}\n{'Reservada' if oc else 'Libre'}", width=96, height=52,
                         corner_radius=10, fg_color=AMB_BG if oc else OK_BG, text_color=AMB if oc else OK,
                         font=f(12, True)).grid(row=k // 5, column=k % 5, padx=6, pady=6)

    # ----- 3. ASIGNACIÓN DE TAREAS -----
    def build_asignar(self):
        v = self.views["Asignación de Tareas"] = ctk.CTkFrame(self.cont, fg_color=BG)
        v.columnconfigure(1, weight=1)
        v.rowconfigure(0, weight=1)
        self.card_emp = card(v)
        self.card_emp.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        der = card(v)
        der.grid(row=0, column=1, sticky="nsew")
        self.emp_titulo = ctk.CTkLabel(der, text="", font=f(18, True), text_color=INK)
        self.emp_titulo.pack(anchor="w", padx=22, pady=(18, 0))
        ctk.CTkLabel(der, text="Tareas actuales", text_color=MUTED, font=f(13)).pack(anchor="w", padx=22)
        self.lista_asig = ctk.CTkFrame(der, fg_color="transparent")
        self.lista_asig.pack(fill="x", padx=22, pady=6)
        ctk.CTkFrame(der, height=1, fg_color=LINE).pack(fill="x", padx=22, pady=8)
        form = ctk.CTkFrame(der, fg_color="transparent")
        form.pack(fill="x", padx=22)
        ctk.CTkLabel(form, text="Nueva tarea", font=f(16, True), text_color=INK).pack(anchor="w")
        self.t_desc = campo(form, "Descripción de la tarea", "Ej. Limpiar la cocina")
        self.t_prio = lista(form, "Prioridad", ["Seleccionar…", "Alta", "Media", "Baja"])
        self.t_msg = msg_label(form)
        self.t_msg.pack(fill="x", pady=(14, 0))
        boton(form, "Guardar tarea", self.guardar_tarea).pack(anchor="e", pady=(14, 18))

    def sel_emp(self, nombre):
        self.emp_sel = nombre
        mensaje(self.t_msg)
        self.pintar_asignar()

    def pintar_asignar(self):
        for w in self.card_emp.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.card_emp, text="Empleados", font=f(16, True), text_color=INK
                     ).pack(anchor="w", padx=16, pady=(16, 6))
        for n, rol in EMPLEADOS:
            sel = n == self.emp_sel
            ctk.CTkButton(self.card_emp, text=f"{n}\n{rol} · {len(self.tareas[n])} tareas", anchor="w",
                          width=230, height=54, corner_radius=10, font=f(13, True), text_color=INK,
                          fg_color="#f1eeff" if sel else "transparent", hover_color="#ece9ff",
                          border_width=2 if sel else 0, border_color=P,
                          command=lambda n=n: self.sel_emp(n)).pack(padx=12, pady=3)
        self.emp_titulo.configure(text=self.emp_sel)
        for w in self.lista_asig.winfo_children():
            w.destroy()
        if not self.tareas[self.emp_sel]:
            ctk.CTkLabel(self.lista_asig, text="Sin tareas asignadas todavía.", text_color=MUTED).pack(anchor="w", pady=6)
        for t, p in self.tareas[self.emp_sel]:
            fila = ctk.CTkFrame(self.lista_asig, fg_color="transparent")
            fila.pack(fill="x", pady=4)
            ctk.CTkLabel(fila, text=t, text_color=INK, font=f(14)).pack(side="left")
            badge(fila, p).pack(side="right")

    def guardar_tarea(self):
        t, p = self.t_desc.get().strip(), self.t_prio.get()
        if not t:
            mensaje(self.t_msg, "Escribe la descripción de la tarea.")
            return
        if p.startswith("Seleccionar"):
            mensaje(self.t_msg, "Error: Debes seleccionar una prioridad para la tarea.")
            return
        self.tareas[self.emp_sel].append((t, p))
        if self.emp_sel == "Juan M.":
            self.mis.append({"t": t, "p": p, "ok": False})
        self.t_desc.delete(0, "end")
        self.t_prio.set("Seleccionar…")
        self.pintar_asignar()
        self.pintar_mis()
        mensaje(self.t_msg, f"Tarea asignada a {self.emp_sel} correctamente.", ok=True)

    # ----- 4. MIS TAREAS -----
    def build_mis(self):
        v = self.views["Mis Tareas"] = ctk.CTkFrame(self.cont, fg_color=BG)
        c = card(v)
        c.pack(fill="both", expand=True)
        self.tabla_mis = ctk.CTkScrollableFrame(c, fg_color="transparent")
        self.tabla_mis.pack(fill="both", expand=True, padx=8, pady=8)
        self.tabla_mis.columnconfigure(1, weight=1)

    def pintar_mis(self):
        for w in self.tabla_mis.winfo_children():
            w.destroy()
        for i, h in enumerate(["Hecha", "Tarea", "Prioridad", "Estado"]):
            ctk.CTkLabel(self.tabla_mis, text=h, text_color=MUTED, font=f(13, True), anchor="w"
                         ).grid(row=0, column=i, sticky="w", padx=10, pady=(2, 8))
        for n, t in enumerate(self.mis, start=1):
            cb = ctk.CTkCheckBox(self.tabla_mis, text="", width=28, fg_color=P, hover_color="#5538d6",
                                 command=lambda i=n - 1: self.toggle(i))
            cb.grid(row=n, column=0, padx=10, pady=8)
            if t["ok"]:
                cb.select()
            ctk.CTkLabel(self.tabla_mis, text=t["t"], anchor="w",
                         text_color=MUTED if t["ok"] else INK,
                         font=f(14, overstrike=t["ok"])).grid(row=n, column=1, sticky="w", padx=10)
            badge(self.tabla_mis, t["p"]).grid(row=n, column=2, padx=10)
            badge(self.tabla_mis, "Completada" if t["ok"] else "Pendiente").grid(row=n, column=3, padx=10)

    def toggle(self, i):
        self.mis[i]["ok"] = not self.mis[i]["ok"]
        self.pintar_mis()
        if self.mis[i]["ok"]:
            self.toast("Tarea marcada como completada")

    # ----- 5. PROVEEDORES -----
    def build_proveedores(self):
        v = self.views["Proveedores"] = ctk.CTkFrame(self.cont, fg_color=BG)
        v.columnconfigure(1, weight=1)
        v.rowconfigure(0, weight=1)
        izq = card(v)
        izq.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        ctk.CTkLabel(izq, text="Proveedores", font=f(16, True), text_color=INK).pack(anchor="w", padx=16, pady=(16, 6))
        for i, (n, d) in enumerate([("Carnes del Goce", "Carnes y embutidos"),
                                    ("Verduras Frescas", "Frutas y verduras"), ("Lácteos Boyacá", "Leche y quesos")]):
            ctk.CTkButton(izq, text=f"{n}\n{d}", anchor="w", width=230, height=54, corner_radius=10,
                          font=f(13, True), text_color=INK, fg_color="#f1eeff" if i == 0 else "transparent",
                          hover_color="#ece9ff", border_width=2 if i == 0 else 0, border_color=P,
                          command=lambda n=n: self.o_prov.set(n)).pack(padx=12, pady=3)
        der = card(v)
        der.grid(row=0, column=1, sticky="nsew")
        form = ctk.CTkFrame(der, fg_color="transparent")
        form.pack(fill="x", padx=22, pady=18)
        ctk.CTkLabel(form, text="Nueva Orden de Compra", font=f(18, True), text_color=INK).pack(anchor="w")
        self.o_prov = lista(form, "Proveedor", ["Carnes del Goce", "Verduras Frescas", "Lácteos Boyacá"])
        self.o_prod = lista(form, "Producto", ["Seleccionar…", "Carne", "Pollo", "Cerdo", "Pescado"])
        self.o_cant = campo(form, "Cantidad", "10")
        self.o_uni = lista(form, "Unidad", ["kilos", "unidades", "litros"])
        self.o_fecha = campo(form, "Entrega solicitada", "Ej. 2026-10-12")
        self.o_msg = msg_label(form)
        self.o_msg.pack(fill="x", pady=(14, 0))
        boton(form, "Enviar pedido", self.enviar_orden).pack(anchor="e", pady=(14, 0))

    def enviar_orden(self):
        prod, cant = self.o_prod.get(), self.o_cant.get().strip()
        if prod.startswith("Seleccionar") or not cant.isdigit() or int(cant) < 1:
            mensaje(self.o_msg, "Selecciona un producto e indica la cantidad.")
            return
        mensaje(self.o_msg, f"Pedido enviado a {self.o_prov.get()}: {cant} {self.o_uni.get()} de {prod}.", ok=True)
        self.o_prod.set("Seleccionar…")
        self.o_cant.delete(0, "end")

    def mainloop(self, n=0):
        self.pintar_reservas()
        self.pintar_asignar()
        self.pintar_mis()
        super().mainloop(n)


if __name__ == "__main__":
    App().mainloop()