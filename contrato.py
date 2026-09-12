"""
contrato.py

Define la representacion del contrato institucional y los valores
permitidos que comparten el resto de modulos del integrador.
"""

from dataclasses import dataclass, asdict
from typing import Optional

# Valores institucionales permitidos para el campo "origen"
ORIGENES_VALIDOS = {"proveedor_a", "proveedor_b"}

CAMPOS_CONTRATO = [
    "ciudad",
    "pais",
    "latitud",
    "longitud",
    "temperatura_c",
    "humedad",
    "viento_kmh",
    "fecha_hora",
    "origen",
]


@dataclass
class Medicion:
    """Representa un registro ya normalizado al contrato institucional."""

    ciudad: Optional[str]
    pais: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    temperatura_c: Optional[float]
    humedad: Optional[float]
    viento_kmh: Optional[float]
    fecha_hora: Optional[str]
    origen: Optional[str]

    def to_api_body(self) -> dict:
        """Cuerpo exacto que exige la API (solo los campos del contrato)."""
        return {campo: getattr(self, campo) for campo in CAMPOS_CONTRATO}

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RegistroProcesado:
    """
    Envoltorio de trazabilidad que acompana a cada medicion durante todo
    el pipeline (lectura -> normalizacion -> validacion -> envio -> reporte).
    """

    id_trazabilidad: str
    fuente: str  # "proveedor_a" | "proveedor_b"
    medicion: Optional[Medicion] = None
    estado: str = "pendiente"
    detalle: Optional[str] = None
    respuesta_api: Optional[dict] = None
    codigo_http: Optional[int] = None
    intentos: int = 0

    def to_dict(self) -> dict:
        return {
            "id_trazabilidad": self.id_trazabilidad,
            "fuente": self.fuente,
            "estado": self.estado,
            "detalle": self.detalle,
            "codigo_http": self.codigo_http,
            "intentos": self.intentos,
            "respuesta_api": self.respuesta_api,
            "medicion": self.medicion.to_dict() if self.medicion else None,
        }
