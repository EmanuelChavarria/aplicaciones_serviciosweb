from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.database.connection import get_db
from app.schemas.medicion import MedicionOut, UltimaMedicionOut
from app.utils.tiempo import desde_hora_local, formatear_hora_colombia

router = APIRouter(tags=["Mediciones"])


@router.get("/mediciones/{medicion_id}", response_model=MedicionOut, summary="Consultar una medición por id")
def obtener_medicion(medicion_id: int, db: Session = Depends(get_db)):
    medicion = crud_medicion.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail=f"No existe la medición con id {medicion_id}")
    return MedicionOut.desde_orm(medicion)


@router.get(
    "/sensores/{sensor_id}/mediciones",
    response_model=list[MedicionOut],
    summary="Histórico de mediciones de un sensor (filtros combinables)",
)
def listar_mediciones_de_sensor(
    sensor_id: int,
    magnitud: str | None = Query(None, description="Nombre de la magnitud, p. ej. temperature"),
    desde: datetime | None = Query(
        None, description="Inicio del rango. Sin zona horaria se interpreta como hora de Colombia."
    ),
    hasta: datetime | None = Query(
        None, description="Fin del rango. Sin zona horaria se interpreta como hora de Colombia."
    ),
    limit: int | None = Query(None, ge=1, le=10000, description="Últimas N mediciones"),
    db: Session = Depends(get_db),
):
    if crud_sensor.get(db, sensor_id) is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")

    desde_utc = desde_hora_local(desde) if desde else None
    hasta_utc = desde_hora_local(hasta) if hasta else None
    if desde_utc and hasta_utc and desde_utc > hasta_utc:
        raise HTTPException(status_code=400, detail="'desde' no puede ser posterior a 'hasta'")

    if magnitud is not None:
        magnitudes = {m.magnitud for m in crud_sensor_magnitud.list_by_sensor(db, sensor_id)}
        if magnitud not in magnitudes:
            raise HTTPException(
                status_code=404,
                detail=f"El sensor {sensor_id} no mide la magnitud '{magnitud}'. "
                f"Disponibles: {sorted(magnitudes)}",
            )

    mediciones = crud_medicion.list_by_sensor(
        db, sensor_id, magnitud=magnitud, desde=desde_utc, hasta=hasta_utc, limit=limit
    )
    return [MedicionOut.desde_orm(m) for m in mediciones]


@router.get(
    "/sensores/{sensor_id}/ultima-medicion",
    response_model=UltimaMedicionOut,
    summary="Última medición de un sensor (todas las magnitudes del payload más reciente)",
)
def obtener_ultima_medicion(sensor_id: int, db: Session = Depends(get_db)):
    sensor = crud_sensor.get(db, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"No existe el sensor con id {sensor_id}")

    mediciones = crud_medicion.ultima_by_sensor(db, sensor_id)
    if not mediciones:
        raise HTTPException(
            status_code=404, detail=f"El sensor {sensor_id} aún no tiene mediciones almacenadas"
        )

    return UltimaMedicionOut(
        sensor_id=sensor.id,
        sensor_codigo=sensor.codigo,
        timestamp_colombia=formatear_hora_colombia(mediciones[0].timestamp_utc),
        mediciones=[MedicionOut.desde_orm(m) for m in mediciones],
    )
