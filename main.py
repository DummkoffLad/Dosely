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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._edit_index = None
        self._reminder_handles = {}

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

    @staticmethod
    def _format_number(value):
        if value in (None, ""):
            return ""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if abs(number - int(number)) < 1e-9:
            return str(int(number))
        text = f"{number:.6g}"
        return text.rstrip("0").rstrip(".") if "." in text else text

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
        self._edit_index = None
        self.root.current = "add"
        self._populate_form("add", prefill or {})

    def open_edit(self, index, *_args):
        meds = backend.load_meds()
        if not (0 <= index < len(meds)):
            toast("No se encontró el medicamento seleccionado")
            return
        self._edit_index = index
        self._populate_form("edit", meds[index])
        self.root.current = "edit"
        
    def _populate_form(self, screen_name, data):
        screen = self.root.get_screen(screen_name)
        ids = screen.ids
        entry = data or {}

        ids.name_field.text = entry.get("nombre", "")
        ids.subs_field.text = entry.get("sustancia", "")
        ids.mg_field.text = self._format_number(entry.get("mg"))
        ids.rx_switch.active = bool(entry.get("requiere_receta", False))
        ids.notes_field.text = entry.get("notas", "")

        reminder = entry.get("recordatorio") or {}
        ids.delay_field.text = self._format_number(reminder.get("intervalo"))
        unit_label = reminder.get("unidad", "horas") or "horas"
        ids.unit_item.text = unit_label

    def reset_form_scroll(self, screen_name):
        """Ensure form screens open at the top position with no focus."""
        def _apply(_dt):
            try:
                screen = self.root.get_screen(screen_name)
                scroll = screen.ids.get("form_scroll")
                if scroll:
                    scroll.scroll_y = 1
                for wid in ("delay_field", "name_field", "subs_field", "mg_field", "notes_field"):
                    if wid in screen.ids:
                        screen.ids[wid].focus = False
            except Exception:
                pass
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

        for idx, med in enumerate(meds):
            nombre = med.get("nombre", "Desconocido")
            sust = med.get("sustancia", "")
            mg = med.get("mg")
            mg_txt_val = self._format_number(mg)
            mg_txt = f"{mg_txt_val} mg" if mg_txt_val else ""
            receta = " • Requiere receta" if med.get("requiere_receta") else ""
            reminder = med.get("recordatorio") or {}
            reminder_txt = ""
            if reminder.get("intervalo"):
                interval_txt = self._format_number(reminder.get("intervalo"))
                unit_txt = reminder.get("unidad", "horas")
                reminder_txt = f" • Cada {interval_txt} {unit_txt}"
            primary = f"{nombre} {mg_txt}".strip()
            secondary = f"{sust}{receta}{reminder_txt}".strip()

            item = TwoLineListItem(
                text=primary if primary else nombre,
                secondary_text=secondary if secondary else "",
                on_release=partial(self.open_edit, idx),
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
            mg_txt_val = self._format_number(mg)
            mg_txt = f"{mg_txt_val} mg" if mg_txt_val else ""
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
    def save_med(self, screen_name="add"):
        """Valida y guarda un medicamento desde la pantalla indicada."""
        entry = self._collect_entry_from_form(screen_name)
        if entry is None:
            return

        try:
            if screen_name == "edit":
                if self._edit_index is None:
                    toast("No hay un medicamento seleccionado para editar")
                    return
                backend.update_med(self._edit_index, entry)
                index = self._edit_index
                toast_msg = "Medicamento actualizado"
            else:
                index = backend.add_med(entry)
                toast_msg = "Medicamento guardado"

            reminder = entry.get("recordatorio") or {}
            delay_txt = self._format_number(reminder.get("intervalo"))
            summary_unit = reminder.get("unidad", "horas")

            try:
                self._schedule_reminder_for_entry(index, entry)
            except Exception as reminder_error:
                toast(f"Guardado, pero el recordatorio falló: {reminder_error}")
            else:
                toast(f"{toast_msg}. Recordatorio cada {delay_txt} {summary_unit}")

            self._edit_index = None
            self.back_to_home()
            self.refresh_home()
        except Exception as e:
            toast(f"Error al guardar: {e}")

    def _collect_entry_from_form(self, screen_name):
        screen = self.root.get_screen(screen_name)
        ids = screen.ids

        nombre = (ids.name_field.text or "").strip()
        sust = (ids.subs_field.text or "").strip()
        mg_text = (ids.mg_field.text or "").strip().replace(",", ".")
        rx = bool(ids.rx_switch.active)
        notas = (ids.notes_field.text or "").strip()
        delay_text = (ids.delay_field.text or "").strip().replace(",", ".")
        unit_label = (ids.unit_item.text or "horas").strip().lower()

        if not delay_text:
            toast("Indique cada cuántas horas se repetirá el recordatorio")
            return None
        try:
            delay_value = float(delay_text)
        except ValueError:
            toast("Ingrese un valor numérico válido para el recordatorio")
            return None
        if delay_value <= 0:
            toast("El recordatorio debe ser mayor que 0")
            return None

        if not nombre:
            toast("El nombre es obligatorio")
            return None

        mg = None
        if mg_text:
            try:
                mg_value = float(mg_text)
            except ValueError:
                toast("Ingrese un valor numérico válido para mg")
                return None
            mg = int(mg_value) if abs(mg_value - int(mg_value)) < 1e-9 else mg_value

        unit_label = "dias" if unit_label.startswith("dia") else "horas"
        unit_en = "days" if unit_label == "dias" else "hours"
        delay_clean = int(delay_value) if abs(delay_value - int(delay_value)) < 1e-9 else delay_value

        message = f"Recordatorio de {nombre}" if nombre else "Recordatorio de medicación"
        reminder = {
            "intervalo": delay_clean,
            "unidad": unit_label,
            "unidad_en": unit_en,
            "intervalo_horas": delay_clean if unit_en == "hours" else delay_clean * 24,
            "mensaje": message,
            "repetir": True,
        }

        entry = {
            "nombre": nombre,
            "sustancia": sust,
            "mg": mg,
            "requiere_receta": rx,
            "notas": notas,
            "recordatorio": reminder,
        }
        return entry

    def _schedule_reminder_for_entry(self, index, entry):
        reminder = entry.get("recordatorio") or {}
        intervalo = reminder.get("intervalo")
        unidad_en = reminder.get("unidad_en")
        mensaje = reminder.get("mensaje") or "Recordatorio de medicación"
        repetir = reminder.get("repetir", False)

        if not intervalo or not unidad_en:
            return None

        previous = self._reminder_handles.pop(index, None)
        if previous and hasattr(previous, "cancel"):
            try:
                previous.cancel()
            except Exception:
                pass

        handler = notify.schedule_notification(intervalo, unidad_en, "Dosely", mensaje, repeat=repetir)
        self._reminder_handles[index] = handler
        return handler

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
            scroll = screen.ids.get("form_scroll") or screen.ids.get("add_scroll") or screen.ids.get("scroll")
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
        """Programa un recordatorio recurrente desde la pantalla de alta."""
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
            unit_label = "dias" if unit_label.startswith("dia") else "horas"
            unit_en = "days" if unit_label == "dias" else "hours"

            nombre = (add_screen.ids.name_field.text or "").strip()
            message = f"Recordatorio de {nombre}" if nombre else "Recordatorio de medicación"

            delay_clean = int(delay) if abs(delay - int(delay)) < 1e-9 else delay
            notify.schedule_notification(delay_clean, unit_en, "Dosely", message, repeat=True)
            toast(f"Recordatorio programado cada {delay_clean} {unit_label}")
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
            notify.schedule_notification(0.002, "hours", "Dosely", "Recordatorio programado (0.002h)")
            toast("Notificaciones enviadas")
        except Exception as e:
            toast(f"No se pudo enviar notificación: {e}")


if __name__ == "__main__":
    # Asegurarse de que ui.kv se encuentre en el directorio de trabajo.
    if not os.path.exists("ui.kv"):
        sys.stderr.write("ERROR: ui.kv no encontrado. Asegúrese de ejecutar en el directorio del proyecto.\n")
        sys.exit(1)
    DoselyApp().run()