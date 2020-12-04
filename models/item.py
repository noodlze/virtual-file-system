from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean
)
from datetime import datetime
from models import Base
from models import with_row_locks


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime)
    size = Column(Integer, default=0)
    is_dir = Column(Boolean, default=False)

    def __init__(self, name, updated_at, size=0, is_dir=False):
        self.name = name
        self.size = size
        self.is_dir = False
        self. updated_at = updated_at

    @staticmethod
    def add_item(name, db, updated_at=datetime.now(), size=0, is_dir=False):
        print("Adding to item table name={} updated_at={} size={} is_dir={}".format(
            name, updated_at, size, is_dir))
        new_item = Item(name, updated_at, size, is_dir)

        db.session.add(new_item)
        db.session.flush()

        return new_item.id

    def update_item_size(self, size, db):
        self.size = size

        db.session.add(self)

    @staticmethod
    def delete_item(id, db):
        print("Deleting from item table id={}".format(id))
        item = with_row_locks(db.session.query(Item), of=Item).filter(
            Item.id == id).first()

        db.session.delete(item)
