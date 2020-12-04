
from sqlalchemy.sql.sqltypes import INTEGER, STRINGTYPE, TEXT
from models import db, with_row_locks
from models.item import Item
from sqlalchemy.orm import backref, relationship
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    select,
    Text
)
from sqlalchemy.sql.functions import concat
from sqlalchemy.sql.expression import cast, literal


class Ancestors(db.Model):
    __tablename__ = "ancestors"

    parent_id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    child_id = Column(Integer, ForeignKey('item.id'),  primary_key=True)
    depth = Column(Integer)
    rank = Column(Text)

    # parent_item = relationship(Item, backref)

    def __init__(self, parent_id, child_id, depth=0, rank=''):
        self.parent_id = parent_id
        self.child_id = child_id
        self.depth = depth
        self.rank = rank

    @staticmethod
    def add_item(child_id, parent_id=None):
        """
        docstring
        """
        print("Adding to ancestor table child_id={} parent_id={}".format(
            child_id, parent_id))
        new_root = Ancestors(child_id, child_id, 0, f'{child_id}')

        if parent_id != None:
            select_parent_rows = with_row_locks(db.session.query(
                Ancestors.parent_id,
                literal(child_id, INTEGER),
                Ancestors.depth + 1,
                cast(concat(Ancestors.rank, ",",
                            literal(f'{child_id}', STRINGTYPE)), TEXT)),
                of=Ancestors).filter(Ancestors.child_id == parent_id).all()

            new_ancestors = [Ancestors(p, c, d, r)
                             for p, c, d, r in select_parent_rows]
            db.session.add_all(new_ancestors)

        db.session.add(new_root)

    @staticmethod
    def delete_item(id):
        print("Deleting from ancestor table id={}".format(id))
        select_parent_rows = with_row_locks(db.session.query(
            Ancestors), of=Ancestors).filter(Ancestors.child_id == id)

        select_child_ids = with_row_locks(
            db.session.query(Ancestors.child_id), of=Ancestors).filter(Ancestors.parent_id == id).all()

        select_subtree_rows = with_row_locks(db.session.query(
            Ancestors), of=Ancestors).filter(Ancestors.child_id.in_(select_child_ids)).all()

        db.session.delete(select_parent_rows)
        db.session.delete(select_subtree_rows)
