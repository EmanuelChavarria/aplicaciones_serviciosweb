from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MedicionEstudianteBase(BaseModel):
    estudiante_id: int
    variable: str
    valor: float
    unidad: str
    fecha_hora: datetime

class MedicionEstudianteCreate(MedicionEstudianteBase):
    pass

class MedicionEstudianteUpdate(BaseModel):
    estudiante_id: int | None = None
    variable: str | None = None
    valor: float | None = None
    unidad: str | None = None
    fecha_hora: datetime | None = None

class MedicionEstudianteResponse(MedicionEstudianteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int