"""Ejemplo que supera el CAPTCHA slider de DataDome y guarda los resultados en CSV.
Funciona en local (Windows) y en GitHub Actions (Linux con pantalla virtual Xvfb)."""
import csv
import os
import sys
from datetime import datetime
from seleniumbase import SB

URL = "https://www.idealista.com/venta-viviendas/barcelona-provincia/"
BASE = "https://www.idealista.com"
CARPETA = "resultados"


def texto(elemento, selector):
    """Devuelve el texto de un subelemento o cadena vacía si no existe."""
    try:
        el = elemento.query_selector(selector)
        return el.text.strip() if el else ""
    except Exception:
        return ""


def enlace(elemento, selector):
    """Devuelve la URL absoluta del enlace o cadena vacía si no existe."""
    try:
        el = elemento.query_selector(selector)
        href = el.get_attribute("href") if el else ""
        if href and href.startswith("/"):
            href = BASE + href
        return href or ""
    except Exception:
        return ""


def detalles(elemento):
    """Devuelve los detalles (habitaciones, m², planta...) separados por ' | '."""
    try:
        spans = elemento.query_selector_all("span.item-detail")
        return " | ".join(s.text.strip() for s in spans if s.text)
    except Exception:
        return ""


os.makedirs(CARPETA, exist_ok=True)
resultados = []

# xvfb=True solo tiene efecto en Linux (GitHub Actions); en Windows se ignora.
with SB(uc=True, test=True, locale="es", xvfb=True) as sb:
    sb.activate_cdp_mode()
    sb.goto(URL)
    sb.sleep(1.5)
    sb.solve_captcha()
    sb.sleep(2)
    sb.click_if_visible("button#didomi-notice-agree-button", timeout=3)

    # Captura de pantalla para depurar (útil sobre todo en GitHub Actions)
    sb.save_screenshot("pantalla.png", folder=CARPETA)

    try:
        print("*** " + sb.get_text("h1"))
    except Exception:
        print("*** No se encontró el título (h1). ¿Bloqueo de DataDome?")

    items = sb.find_elements("div.item-info-container")
    for item in items:
        item.flash(color="44CC88")
        fila = {
            "titulo": texto(item, "a.item-link"),
            "precio": texto(item, "span.item-price"),
            "detalles": detalles(item),
            "url": enlace(item, "a.item-link"),
        }
        print(fila["titulo"])
        print(fila["precio"])
        resultados.append(fila)

# Guardar CSV (utf-8-sig y ';' para que Excel en español lo abra bien)
nombre = os.path.join(CARPETA, f"idealista_{datetime.now():%Y%m%d_%H%M%S}.csv")
with open(nombre, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f, fieldnames=["titulo", "precio", "detalles", "url"], delimiter=";"
    )
    writer.writeheader()
    writer.writerows(resultados)

print(f"\n{len(resultados)} anuncios guardados en {nombre}")

# Si no hay resultados, marcar la ejecución como fallida
if not resultados:
    sys.exit(1)