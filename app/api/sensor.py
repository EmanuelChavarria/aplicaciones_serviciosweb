from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.database.connection import get_db
from app.schemas.sensor import SensorOut

router = APIRouter(prefix="/sensores", tags=["Sensores"])


@router.get("", response_model=list[SensorOut], summary="Listar sensores")
def listar_sensores(db: Session = Depends(get_db)):
    return crud_sensor.list_all(db)


# Esta ruta va ANTES de "/{sensor_id}" para que "por-codigo" nunca se confunda con un id.
@router.get(
    "/por-codigo/{codigo}",
    response_model=SensorOut,
    summary="Consultar un sensor por su código (p. ej. TEST-001)",
)
def obtener_sensor_por_codigo(codigo: str, db: Session = Depends(get_db)):
    sensor = crud_sensor.get_by_codigo(db, codigo)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe un sensor con código '{codigo}'")
    return sensor


@router.get("/{sensor_id}", response_model=SensorOut, summary="Consultar un sensor por id")
def obtener_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = crud_sensor.get(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")
    return sensor
