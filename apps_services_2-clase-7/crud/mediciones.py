from sqlalchemy import select
from sqlalchemy.orm import Session
from models.estudiante import MedicionEstudiante
from schemas.estudiante import MedicionEstudianteCreate, MedicionEstudianteUpdate

def get_all(db: Session) -> list[MedicionEstudiante]:
    return list(db.scalars(select(MedicionEstudiante).order_by(MedicionEstudiante.id)).all())

def get(db: Session, medicion_id: int) -> MedicionEstudiante | None:
    return db.get(MedicionEstudiante, medicion_id)

def create(db: Session, data: MedicionEstudianteCreate) -> MedicionEstudiante:
    medicion = MedicionEstudiante(**data.model_dump())
    db.add(medicion)
    db.commit()
    db.refresh(medicion)
    return medicion

def update(db: Session, medicion: MedicionEstudiante, data: MedicionEstudianteUpdate) -> MedicionEstudiante:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(medicion, field, value)
    db.commit()
    db.refresh(medicion)
    return medicion

def delete(db: Session, medicion: MedicionEstudiante) -> None:
    db.delete(medicion)
    db.commit()