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
from utils.db_session import provide_db_session


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
        self.is_dir = is_dir
        self. updated_at = updated_at

    @staticmethod
    @provide_db_session
    def add_item(name, db=None, updated_at=datetime.now(), size=0, is_dir=False):
        print("Adding to item table name={} updated_at={} size={} is_dir={}".format(
            name, updated_at, size, is_dir))
        new_item = Item(name, updated_at, size, is_dir)

        db.session.add(new_item)
        db.session.flush()

        return new_item.id

    @provide_db_session
    def update_item_size(self, size, db=None):
        self.size = size

        db.session.add(self)

    @staticmethod
    @provide_db_session
    def delete_item(id, db=None):
        print("Deleting from item table id={}".format(id))
        item = with_row_locks(db.session.query(Item).filter(
            Item.id == id), of=Item).first()

        db.session.delete(item)

    @staticmethod
    @provide_db_session
    def is_a_dir(id, db=None):
        item = with_row_locks(db.session.query(
            Item.is_dir).filter(Item.id == id)).first()
        if item:
            return True if item[0] else False
        return False
