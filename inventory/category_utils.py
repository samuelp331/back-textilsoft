"""Normalización y deduplicación lógica de categorías de producto (texto libre en BD)."""

from __future__ import annotations

from inventory.models import Producto


def normalize_categoria_text(value: str | None) -> str:
    """Recorta bordes y colapsa espacios internos."""
    return " ".join((value or "").split())


def find_canonical_categoria(normalized: str) -> str | None:
    """
    Si ya existe un producto con categoría equivalente (mismo texto normalizado,
    comparación sin distinguir mayúsculas), devuelve la cadena tal como está en BD.
    Si no hay coincidencia, devuelve None.
    """
    if not normalized:
        return None
    key = normalized.lower()
    for stored in Producto.objects.values_list("categoria", flat=True).distinct():
        if stored is None:
            continue
        candidate = normalize_categoria_text(str(stored))
        if not candidate:
            continue
        if candidate.lower() == key:
            return candidate
    return None


def unique_categorias_for_list() -> list[str]:
    """Lista de categorías únicas para filtros/UI, agrupadas sin distinguir mayúsculas ni espacios."""
    seen: dict[str, str] = {}
    for raw in Producto.objects.values_list("categoria", flat=True):
        display = normalize_categoria_text("" if raw is None else str(raw))
        if not display:
            continue
        lk = display.lower()
        if lk not in seen:
            seen[lk] = display
    return sorted(seen.values(), key=lambda x: x.lower())
