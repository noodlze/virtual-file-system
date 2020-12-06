
from sqlalchemy.sql.sqltypes import INTEGER, STRINGTYPE, TEXT
from models import Base
from models import with_row_locks
from models.item import Item
from sqlalchemy.orm import backref, relationship
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    select,
    Text,
    and_
)
from datetime import datetime
from sqlalchemy.sql.functions import concat
from sqlalchemy.sql.expression import cast, literal
from utils.db_session import provide_db_session


class Ancestors(Base):
    __tablename__ = "ancestors"

    parent_id = Column(Integer, ForeignKey('item.id'))
    child_id = Column(Integer, ForeignKey('item.id'))
    depth = Column(Integer)
    rank = Column(Text, primary_key=True)

    # parent_item = relationship(Item, backref)

    def __init__(self, parent_id, child_id, depth=0, rank=''):
        self.parent_id = parent_id
        self.child_id = child_id
        self.depth = depth
        self.rank = rank

    @staticmethod
    @provide_db_session
    def add_item(child_id, db=None, parent_id=None):
        """
        Add a rel between child and itself(depth=0)
        Add relationships between child and item in UPPER TREE
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
    @provide_db_session
    def delete_item(id, db=None, subtree=True, upper_tree=True):
        """
        updates parent size and updated_at(if dir)

        deletes UPPER TREE(default=True, optional): relations between parent directories(many lvls up) and item

        deletes SUB TREE(default=True, optional): relations between item and contents (if directory)
        """
        # UPDATE parent item
        parent_id = with_row_locks(db.session.query(Ancestors.parent_id), of=Ancestors).filter(
            and_(Ancestors.child_id == id, Ancestors.depth == 1)).first()

        print("parent_id of Item={}".format(parent_id))
        parent_item = with_row_locks(db.session.query(
            Item), of=Item).filter(Item.id == parent_id).first()
        parent_item.update_item_size(
            size=parent_item.size - 1)  # update parent dir size

        if parent_item.is_dir:  # update updated_at() if a directory
            parent_item.updated_at = datetime.now()

        db.session.add(parent_item)

        print("Deleting from ancestor table id={}".format(id))
        # deleting UPPER TREE
        if upper_tree:
            print("Deleting upper tree of item={}".format(id))
            select_parent_rows = with_row_locks(db.session.query(
                Ancestors), of=Ancestors).filter(Ancestors.child_id == id).delete(synchronize_session=False)

        # must get children items
        # deleting SUB TREE

        select_child_ids = with_row_locks(
            db.session.query(Ancestors.child_id), of=Ancestors).filter(Ancestors.parent_id == id).all()

        if subtree:
            print("Deleting upper tree of item={}, contains items={}".format(
                id, select_child_ids))
            select_subtree_rows = with_row_locks(db.session.query(
                Ancestors), of=Ancestors).filter(Ancestors.child_id.in_(select_child_ids)).delete(synchronize_session=False)

        # return the subtree item ids (may be needed by caller)
        return select_child_ids
