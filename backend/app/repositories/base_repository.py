from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Type, List, Optional

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id_val) -> Optional[T]:
        return self.session.query(self.model).filter(self.model.id == id_val).first()

    def get_all(self) -> List[T]:
        return self.session.query(self.model).all()

    def create(self, obj: T) -> T:
        self.session.add(obj)
        return obj

    def delete(self, obj: T) -> None:
        self.session.delete(obj)
