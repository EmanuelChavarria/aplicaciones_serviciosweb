from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import get_db
from app.schemas.sensor_magnitud import SensorMagnitudOut

router = APIRouter(tags=["Magnitudes"])


@router.get(
    "/sensores/{sensor_id}/magnitudes",
    response_model=list[SensorMagnitudOut],
    summary="Magnitudes que mide un sensor",
)
def listar_magnitudes_de_sensor(sensor_id: int, db: Session = Depends(get_db)):
    if crud_sensor.get(db, sensor_id) is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")
    return crud_sensor_magnitud.list_by_sensor(db, sensor_id)


@router.get(
    "/sensor-magnitudes/{sensor_magnitud_id}",
    response_model=SensorMagnitudOut,
    summary="Consultar una relación sensor-magnitud por id",
)
def obtener_sensor_magnitud(sensor_magnitud_id: int, db: Session = Depends(get_db)):
    sm = crud_sensor_magnitud.get(db, sensor_magnitud_id)
    if sm is None:
        raise HTTPException(
            status_code=404, detail=f"No existe la sensor-magnitud con id {sensor_magnitud_id}"
        )
    return sm
