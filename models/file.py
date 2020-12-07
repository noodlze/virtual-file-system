from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text
)
from models import with_row_locks
from models import Base
from utils.db_session import provide_db_session

class File(Base):
    __tablename__ = "file"

    id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    data = Column(Text)

    def __init__(self, id, data):
        self.id = id
        self.data = data

    @staticmethod
    @provide_db_session
    def add_item(file_id, data, db=None):
        print("Adding to file table file_id={} data={}".format(file_id, data))
        new_file = File(file_id, data)

        db.session.add(new_file)

    @staticmethod
    @provide_db_session
    def delete_item(id, db=None):
        print("Deleting from file table id={}".format(id))

        with_row_locks(db.session.query(File).filter(
            File.id == id), of=File).delete()
