# -*- coding: utf-8 -*-
"""
Backend de Dosely: lectura y escritura de JSON,
y funciones para cargar catálogo y buscar.

Archivos:
- storage/medicamentos.json  (lista del usuario)
- storage/catalogo.json      (catálogo base con ejemplos)
"""
import json
import os

# Directorio de almacenamiento relativo al directorio actual
STORAGE_DIR = os.path.join(os.getcwd(), "storage")
MEDS_FILE = os.path.join(STORAGE_DIR, "medicamentos.json")
CATALOG_FILE = os.path.join(STORAGE_DIR, "catalogo.json")


def ensure_storage():
    """
    Crea el directorio 'storage' si no existe.
    """
    if not os.path.isdir(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)


def initialize_empty_meds():
    """
    Inicializa medicamentos.json como lista vacía si no existe.
    """
    ensure_storage()
    if not os.path.exists(MEDS_FILE):
        with open(MEDS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def initialize_default_catalog():
    """
    Inicializa catalogo.json con ~10 medicamentos de ejemplo.
    Solo se ejecuta si el archivo no existe.
    """
    ensure_storage()
    if os.path.exists(CATALOG_FILE):
        return
    sample = [
        {"nombre": "Paracetamol", "sustancia": "Paracetamol", "mg": 500, "requiere_receta": False},
        {"nombre": "Ibuprofeno", "sustancia": "Ibuprofeno", "mg": 400, "requiere_receta": False},
        {"nombre": "Amoxicilina", "sustancia": "Amoxicilina", "mg": 500, "requiere_receta": True},
        {"nombre": "Omeprazol", "sustancia": "Omeprazol", "mg": 20, "requiere_receta": False},
        {"nombre": "Metformina", "sustancia": "Metformina", "mg": 850, "requiere_receta": True},
        {"nombre": "Losartán", "sustancia": "Losartán potásico", "mg": 50, "requiere_receta": True},
        {"nombre": "Atorvastatina", "sustancia": "Atorvastatina cálcica", "mg": 20, "requiere_receta": True},
        {"nombre": "Cetirizina", "sustancia": "Cetirizina diclorhidrato", "mg": 10, "requiere_receta": False},
        {"nombre": "Salbutamol", "sustancia": "Salbutamol", "mg": 100, "requiere_receta": True},
        {"nombre": "Ácido acetilsalicílico", "sustancia": "Aspirina", "mg": 100, "requiere_receta": False},
    ]
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)


def load_meds():
    """
    Devuelve la lista de medicamentos del usuario.
    """
    initialize_empty_meds()
    try:
        with open(MEDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def add_med(entry: dict):
    """
    Añade un medicamento al archivo del usuario.
    entry: dict con claves: nombre, sustancia, mg, requiere_receta, notas
    """
    meds = load_meds()
    meds.append(entry)
    with open(MEDS_FILE, "w", encoding="utf-8") as f:
        json.dump(meds, f, ensure_ascii=False, indent=2)


def load_catalog():
    """
    Devuelve la lista del catálogo base.
    """
    if not os.path.exists(CATALOG_FILE):
        initialize_default_catalog()
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def search_catalog(query: str):
    """
    Busca en el catálogo por nombre o sustancia (insensible a mayúsculas).
    """
    catalog = load_catalog()
    q = (query or "").strip().casefold()
    if not q:
        return catalog
    results = []
    for item in catalog:
        nombre = (str(item.get("nombre", ""))).casefold()
        sust = (str(item.get("sustancia", ""))).casefold()
        if q in nombre or q in sust:
            results.append(item)
    return results