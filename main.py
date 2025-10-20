# -*- coding: utf-8 -*-
"""
Dosely - App sencilla para registrar medicamentos, buscar en un catálogo base,
y recibir notificaciones locales. UI con KivyMD (Material 3) y almacenamiento en JSON.

Requisitos:
- Python 3.11
- Kivy 2.3.0
- KivyMD 1.1.1
- Plyer 2.1.0 o superior

Ejecución en escritorio:
    python main.py

Este proyecto está pensado para poder compilarse a Android con Buildozer.
"""
import os
import sys
from functools import partial

from kivy import require as kivy_require
kivy_require("2.3.0")

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.list import TwoLineListItem
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu

import backend
import notify


class DoselyApp(MDApp):
    """
    Aplicación principal de Dosely.
    Maneja la carga de la UI, la navegación, y la conexión con el backend JSON.
    """

    def build(self):
        # Estilo Material 3 y tema oscuro con colores suaves.
        # En escritorio, forzar relación 9:16 para previsualizar como teléfono.
        if platform in ("win", "linux", "macosx"):
            Window.size = (450, 800)  # 9:16 aprox
            Window.minimum_width = 360
            Window.minimum_height = 640
            # En escritorio evita pan para que no empuje el contenido bajo el AppBar
            Window.softinput_mode = "below_target"
        else:
            # En móviles, que el teclado redimensione la vista para evitar solaparse.
            Window.softinput_mode = "resize"
        
        self.title = "Dosely"
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "Gray"
        self.theme_cls.accent_hue = "50"
        # Cargar archivo .kv
        return Builder.load_file("ui.kv")

    def on_start(self):
        """
        Inicializa almacenamiento, crea archivos si faltan y refresca la pantalla de inicio.
        """
        backend.ensure_storage()
        # Asegurar que el catálogo base exista; si no, crearlo con ejemplos.
        if not os.path.exists(backend.CATALOG_FILE):
            backend.initialize_default_catalog()
        # Crear medicamentos.json si no existe.
        if not os.path.exists(backend.MEDS_FILE):
            backend.initialize_empty_meds()
        # Poblar lista de inicio
        Clock.schedule_once(lambda *_: self.refresh_home(), 0.05)

    # ------------------------
    # Navegación
    # ------------------------
    def open_search(self):
        self.root.current = "search"
        self.clear_search()
        # Mostrar todo el catálogo inicialmente
        catalog = backend.load_catalog()
        self.populate_search_results(catalog)

    def open_add(self, prefill=None):
        self.root.current = "add"
        add_screen = self.root.get_screen("add")
        # Rellenar campos con datos si se proporcionan
        if prefill:
            add_screen.ids.name_field.text = prefill.get("nombre", "")
            add_screen.ids.subs_field.text = prefill.get("sustancia", "")
            mg_val = prefill.get("mg", "")
            add_screen.ids.mg_field.text = str(mg_val) if mg_val is not None else ""
            add_screen.ids.rx_switch.active = bool(prefill.get("requiere_receta", False))
            add_screen.ids.notes_field.text = prefill.get("notas", "")
        else:
            # Limpiar campos
            add_screen.ids.name_field.text = ""
            add_screen.ids.subs_field.text = ""
            add_screen.ids.mg_field.text = ""
            add_screen.ids.rx_switch.active = False
            add_screen.ids.notes_field.text = ""
        
    def reset_add_scroll(self, *_args):
        """Ensure Add screen opens at the top position and no field has focus."""
        def _apply(_dt):
            try:
                add_screen = self.root.get_screen("add")
                scroll = add_screen.ids.get("add_scroll")
                if scroll:
                    scroll.scroll_y = 1
                for wid in ("name_field", "subs_field", "mg_field", "notes_field"):
                    if wid in add_screen.ids:
                        add_screen.ids[wid].focus = False
            except Exception:
                pass
        # Schedule to run after the layout has its final size
        Clock.schedule_once(_apply, 0)
        Clock.schedule_once(_apply, 0.05)

    def back_to_home(self):
        self.root.current = "home"

    def back_to_search(self):
        self.root.current = "search"

    # ------------------------
    # Home
    # ------------------------
    def refresh_home(self):
        """
        Carga medicamentos guardados y los muestra en HomeScreen.
        """
        meds = backend.load_meds()
        home = self.root.get_screen("home")
        list_widget = home.ids.meds_list
        list_widget.clear_widgets()

        if not meds:
            # Estado vacío
            item = TwoLineListItem(
                text="No hay medicamentos guardados",
                secondary_text="Use el botón + para añadir",
                disabled=True,
            )
            list_widget.add_widget(item)
            return

        for med in meds:
            nombre = med.get("nombre", "Desconocido")
            sust = med.get("sustancia", "")
            mg = med.get("mg")
            mg_txt = f"{mg} mg" if mg not in (None, "",) else ""
            receta = " • Requiere receta" if med.get("requiere_receta") else ""
            primary = f"{nombre} {mg_txt}".strip()
            secondary = f"{sust}{receta}".strip()

            item = TwoLineListItem(
                text=primary if primary else nombre,
                secondary_text=secondary if secondary else "",
            )
            list_widget.add_widget(item)

    # ------------------------
    # Búsqueda
    # ------------------------
    def clear_search(self):
        search_screen = self.root.get_screen("search")
        search_screen.ids.search_field.text = ""
        search_screen.ids.results_list.clear_widgets()

    def filter_search(self, query):
        """
        Filtra catálogo por nombre o sustancia.
        """
        results = backend.search_catalog(query or "")
        self.populate_search_results(results)

    def populate_search_results(self, results):
        """
        Llena la lista de resultados con items tocables que abren la pantalla de Añadir.
        """
        search_screen = self.root.get_screen("search")
        list_widget = search_screen.ids.results_list
        list_widget.clear_widgets()

        if not results:
            item = TwoLineListItem(
                text="Sin resultados",
                secondary_text="Pruebe con otro término de búsqueda o",
                disabled=True,
            )
            list_widget.add_widget(item)
            return

        for r in results:
            nombre = r.get("nombre", "")
            sust = r.get("sustancia", "")
            mg = r.get("mg")
            mg_txt = f"{mg} mg" if mg not in (None, "",) else ""
            primary = f"{nombre} {mg_txt}".strip()
            secondary = sust

            item = TwoLineListItem(
                text=primary if primary else nombre,
                secondary_text=secondary,
                on_release=partial(self._open_add_from_result, r),
            )
            list_widget.add_widget(item)

    def _open_add_from_result(self, entry, *_args):
        """
        Abre AddScreen con datos prellenados del catálogo.
        """
        # Asegurar campos esperados
        prefill = {
            "nombre": entry.get("nombre", ""),
            "sustancia": entry.get("sustancia", ""),
            "mg": entry.get("mg", ""),
            "requiere_receta": entry.get("requiere_receta", False),
            "notas": "",
        }
        self.open_add(prefill=prefill)

    # ------------------------
    # Guardado
    # ------------------------
    def save_med(self):
        """
        Lee campos de AddScreen, valida y guarda en medicamentos.json
        """
        add_screen = self.root.get_screen("add")
        nombre = (add_screen.ids.name_field.text or "").strip()
        sust = (add_screen.ids.subs_field.text or "").strip()
        mg_text = (add_screen.ids.mg_field.text or "").strip().replace(",", ".")
        rx = bool(add_screen.ids.rx_switch.active)
        notas = (add_screen.ids.notes_field.text or "").strip()

        # Validación básica
        if not nombre:
            toast("El nombre es obligatorio")
            return

        mg = None
        if mg_text:
            try:
                # Permitir enteros o decimales
                mg = float(mg_text)
                # Redondeo amigable si es entero
                mg = int(mg) if abs(mg - int(mg)) < 1e-9 else mg
            except ValueError:
                toast("Ingrese un valor numérico válido para mg")
                return

        entry = {
            "nombre": nombre,
            "sustancia": sust,
            "mg": mg,
            "requiere_receta": rx,
            "notas": notas,
        }

        try:
            backend.add_med(entry)
            toast("Medicamento guardado")
            self.back_to_home()
            self.refresh_home()
        except Exception as e:
            toast(f"Error al guardar: {e}")

    def ensure_visible(self, screen_name, widget, padding=140):
        """Scroll the screen's ScrollView so `widget` is visible when the soft keyboard shows.
        On desktop (no soft keyboard), do nothing to avoid jumping.
        """
        try:
            # Only act when a soft keyboard is likely present
            is_desktop = platform in ("win", "linux", "macosx")
            if is_desktop and getattr(Window, "keyboard_height", 0) == 0:
                return
            screen = self.root.get_screen(screen_name)
            scroll = screen.ids.get("add_scroll") or screen.ids.get("scroll")
            if scroll and widget:
                Clock.schedule_once(lambda *_: scroll.scroll_to(widget, padding=dp(padding), animate=True), 0)
        except Exception:
            # Silently ignore if scroll or widget are missing
            pass

    # ------------------------
    # Recordatorios
    # ------------------------
    def open_unit_menu(self, caller):
        """Open dropdown to select time unit (horas/dias)."""
        try:
            # Close previous menu if open
            if hasattr(self, "_unit_menu") and self._unit_menu:
                self._unit_menu.dismiss()
        except Exception:
            pass

        items = []
        for label in ("horas", "dias"):
            items.append({
                "viewclass": "OneLineListItem",
                "text": label,
                "on_release": partial(self._select_unit, caller, label),
            })
        try:
            self._unit_menu = MDDropdownMenu(
                caller=caller,
                items=items,
                width_mult=3,
                position="bottom",
            )
            self._unit_menu.open()
        except Exception as e:
            toast(f"No se pudo abrir el menú: {e}")

    def _select_unit(self, caller, label, *_):
        try:
            caller.text = label
            if hasattr(self, "_unit_menu") and self._unit_menu:
                self._unit_menu.dismiss()
        except Exception:
            pass

    def schedule_from_add(self):
        """Schedule a notification based on Add screen delay and unit."""
        try:
            add_screen = self.root.get_screen("add")
            delay_txt = (add_screen.ids.delay_field.text or "").strip().replace(",", ".")
            if not delay_txt:
                toast("Ingrese un tiempo para el recordatorio")
                return
            try:
                delay = float(delay_txt)
            except ValueError:
                toast("Tiempo inválido")
                return
            if delay <= 0:
                toast("El tiempo debe ser mayor que 0")
                return

            unit_label = (add_screen.ids.unit_item.text or "horas").strip().lower()
            unit_en = "hours" if unit_label.startswith("hora") else "days"

            nombre = (add_screen.ids.name_field.text or "").strip()
            message = f"Recordatorio de {nombre}" if nombre else "Recordatorio de medicación"

            notify.schedule_notification(delay, unit_en, "Dosely", message)
            toast(f"Recordatorio programado en {delay} {unit_label}")
        except Exception as e:
            toast(f"No se pudo programar: {e}")

    # ------------------------
    # Notificaciones
    # ------------------------
    def test_notification(self):
        """
        Dispara una notificación inmediata y programa otra a los 5 segundos.
        """
        try:
            notify.send_notification("Dosely", "Este es un recordatorio de prueba")
            notify.schedule_notification(0.002,"hours", "Dosely", "Recordatorio programado (0.002h)")
            toast("Notificaciones enviadas")
        except Exception as e:
            toast(f"No se pudo enviar notificación: {e}")


if __name__ == "__main__":
    # Asegurarse de que ui.kv se encuentre en el directorio de trabajo.
    if not os.path.exists("ui.kv"):
        sys.stderr.write("ERROR: ui.kv no encontrado. Asegúrese de ejecutar en el directorio del proyecto.\n")
        sys.exit(1)
    DoselyApp().run()