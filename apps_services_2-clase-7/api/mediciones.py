from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from crud import estudiante as crud  # Puedes cambiar el import según el nombre de tu archivo crud
from database import get_db
from schemas.mediciones import MedicionEstudianteCreate, MedicionEstudianteResponse, MedicionEstudianteUpdate
router = APIRouter(prefix="/mediciones", tags=["Mediciones"])

@router.get("", response_model=list[MedicionEstudianteResponse])
def listar_mediciones(db: Session = Depends(get_db)):
    return crud.get_all(db)

@router.get("/{medicion_id}", response_model=MedicionEstudianteResponse)
def obtener_medicion(medicion_id: int, db: Session = Depends(get_db)):
    medicion = crud.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    return medicion

@router.post("", response_model=MedicionEstudianteResponse, status_code=status.HTTP_201_CREATED)
def agregar_medicion(data: MedicionEstudianteCreate, db: Session = Depends(get_db)):
    return crud.create(db, data)

@router.put("/{medicion_id}", response_model=MedicionEstudianteResponse)
def reemplazar_medicion(medicion_id: int, data: MedicionEstudianteCreate, db: Session = Depends(get_db)):
    medicion = crud.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    return crud.update(db, medicion, MedicionEstudianteUpdate(**data.model_dump()))

@router.patch("/{medicion_id}", response_model=MedicionEstudianteResponse)
def actualizar_medicion(medicion_id: int, data: MedicionEstudianteUpdate, db: Session = Depends(get_db)):
    medicion = crud.get(db, medicion_id)
    if medicion is None:
        raise HTTPException(status_code=404, detail="La medición no existe")
    return crud.update(db, medicion, data)