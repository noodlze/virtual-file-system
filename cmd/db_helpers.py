from const import BASE_DIR_ID
from datetime import datetime
import os
from sqlalchemy import and_, not_
from models.ancestors import Ancestors
from models.item import Item
from models.file import File
from sqlalchemy import (
    func,
    select
)
from models import with_row_locks
from utils.db_session import provide_db_session


def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


@provide_db_session
def validate_new_item_name(item_name, parent_id, db=None):
    same_folder_items = db.session.query(Ancestors).join(
        Item, Item.id == Ancestors.child_id).filter(Ancestors.parent_id == parent_id).distinct().all()

    if item_name in [item.name for item in same_folder_items]:
        return False
    return True


@provide_db_session
def item_exists(abs_path, db=None, check_is_dir=False):
    """
    Check if item exists,
    if check_is_dir is passed also checks whether item is a dir

    returns (Bool, Int)
        = (whether item exists + is dir(if check requested), item id of deepest child item in path)
    """
    print("checking if item exists abs_path={}".format(abs_path))
    if abs_path == "/":
        return True, BASE_DIR_ID

    allparts = abs_path.split("/")

    # allparts[0] == ""
    root_item = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == BASE_DIR_ID).first()

    parent_item = root_item
    # if abs_path contains many subdirectories
    for item_name in allparts[1:]:  # skips root
        # get parent folder contents
        child_item_ids = db.session.query(Ancestors.child_id).filter(
            Ancestors.parent_id == parent_item.id).distinct().all()

        # check if item exists in parent folder
        child_item = with_row_locks(db.session.query(Item), of=Item).filter(and_(Item.id.in_(child_item_ids),
                                                                                 Item.name == item_name)).first()
        if not child_item:
            # item does not exist in parent
            return False, BASE_DIR_ID

        # item exists in parent
        # update parent item
        parent_item = child_item

    if check_is_dir and not parent_item.is_dir:  # exists but not a dir
        return False, parent_item.id

    # deepest subdirectory (item) id / current directory id
    return True, parent_item.id


@provide_db_session
def list_child_items(parent_id, db=None, depth=1):

    query = db.session.query(Ancestors, Item).filter(and_(Ancestors.parent_id == parent_id,
                                                          Ancestors.depth <= depth,
                                                          Ancestors.depth != 0)).order_by(Ancestors.rank)

    query = query.join(Item, Item.id == Ancestors.child_id).join(
        File, File.id == Ancestors.child_id, isouter=True).all()
    return query

    # with_size = []
    # for r in query.all():

    #     if not r.data:  # a folder
    #         # calculate folder size
    #         f_size = with_row_locks(db.session.query(func.count(Ancestors.parent_id)), of=Ancestors).filter(
    #             Ancestors.parent_id == r.child_id).scalar()
    #         with_size.append(r, f_size)
    #     else:
    #         with_size.append(r, len(r.data))
    # return with_size


@provide_db_session
def get_child_item(parent_id, child_name, db=None):
    """
    given parent id and child name -> return child id else None if doesn't exist

    :param parent_id: [description]
    :type parent_id: [type]
    :param child_name: [description]
    :type child_name: [type]

    """
    r = with_row_locks(db.session.query(Ancestors).join(Item, Item.id == Ancestors.child_id)).filter(and_(Ancestors.parent_id == parent_id),
                                                                                                     Item.name == child_name).first()
    return r.id if r else None


@provide_db_session
def add_new_item(name, item_parent_id, db=None, data=None):
    try:
        print(f'add new item {name} {item_parent_id}')
        # add to item table
        is_dir = True if data == None else False
        size = len(data) if data else 0
        new_item_id = Item.add_item(name=name, size=size, is_dir=is_dir)

        # add to file table
        if data:
            File.add_item(file_id=new_item_id, data=data)

        # add to ancestors table
        Ancestors.add_item(child_id=new_item_id,
                           parent_id=item_parent_id)

        # update item_parent_id size
        parent_item = db.session.query(Item).filter(
            Item.id == item_parent_id).first()

        if parent_item:
            parent_item.update_item_size(size=parent_item.size + 1)
            # Item(id=parent_item.id,
            #      name=parent_item.name,
            #      created_at=parent_item.created_at,
            #      updated_at=parent_item.updated_at,
            #      size=parent_item.size,
            #      is_dir=parent_item.is_dir).update_item_size(parent_item.size + 1)

            db.session.add(parent_item)

        return new_item_id
    except Exception as e:
        db.session.rollback()
        raise e


@provide_db_session
def delete_item(id, db=None):
    # delete from ancestors table
    # NOTE: must delete before item to avoid fk violation
    # returns children items that need to be deleted
    child_item_ids = Ancestors.delete_item(id=id)

    # delete from file table
    # NOTE: must delete before item to avoid fk violation
    with_row_locks(db.session.query(File), of=File).filter(
        File.id.in_(child_item_ids+[id])).delete(synchronize_session=False)

    # delete from item table
    with_row_locks(db.session.query(Item), of=Item).filter(
        Item.id.in_(child_item_ids+[id])).delete(synchronize_session=False)


@provide_db_session
def move_item(id, new_parent_id, db=None):
    # old_parent
    old_parent_id = with_row_locks(db.session.query(Ancestors.parent_id), of=Ancestors).filter(and_(Ancestors.child_id == id,
                                                                                                    Ancestors.depth == 1)).first()

    # define subtree as id + all childs of id
    childs = with_row_locks(db.session.query(
        Ancestors), of=Ancestors).filter(Ancestors.parent_id == id).all()
    subtree_ids = [item.child_id for item in childs]
    subtree = with_row_locks(db.session.query(
        Ancestors), of=Ancestors).filter(Ancestors.parent_id.in_(subtree_ids)).all()

    # delete relationships between upper tree of the tree + subtree
    with_row_locks(db.session.query(
        Ancestors), of=Ancestors).filter(and_(Ancestors.child_id.in_(subtree_ids),
                                              not_(Ancestors.parent_id.in_(subtree_ids)))).delete(synchronize_session=False)

    # add relationships between (new parent + upper tree of new_parent) + subtree
    new_parent_upper_tree = with_row_locks(db.session.query(Ancestors), of=Ancestors).filter(
        Ancestors.child_id == new_parent_id).all()
    for new_upper_item in new_parent_upper_tree:
        upper_parent_id = new_upper_item.parent_id

        # distance from (upper_tree_item -> new_parent_id) = upper_tree_depth
        # from (new_parent -> item_id) = 1
        # from (item_id -> child_id) = subtree_item_depth
        upper_tree_depth = new_upper_item.depth
        upper_tree_rank = new_upper_item.rank

        for subtree_item in childs:
            new_rel = Ancestors(parent_id=upper_parent_id,
                                child_id=subtree_item.child_id,
                                depth=upper_tree_depth + subtree_item.depth + 1,
                                rank=f'{upper_tree_rank},{subtree_item.rank}')
            db.session.add(new_rel)

    # updating old_parent size + updated_at(if dir)
    # updating new_parent size + updated_at(if dir)
    new_parent = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == new_parent_id).first()
    old_parent = with_row_locks(db.session.query(Item), of=Item).filter(
        Item.id == old_parent_id).first()

    if new_parent.is_dir:
        new_parent.updated_at = datetime.now()
        new_parent.size += 1

    if old_parent.is_dir:
        old_parent.updated_at = datetime.now()
        old_parent.size -= 1
    db.session.add(new_parent)
    db.session.add(old_parent)

