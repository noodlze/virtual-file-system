from blueprints import BASE_DIR_ID
from datetime import datetime
import os
from sqlalchemy import and_, not_
from models.ancestors import Ancestors
from models.item import Item
from models.file import File
from sqlalchemy import (
    func,
    select,
    not_
)
from models import db, with_row_locks


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


def validate_new_item_name(item_name, parent_id):
    same_folder_items = db.session.query(Ancestors).join(
        Item, Item.id == Ancestors.child_id).filter(Ancestors.parent_id == parent_id).distinct().all()

    if item_name in [item.name for item in same_folder_items]:
        return False
    return True


def item_exists(abs_path):
    if abs_path == "/":
        return True, BASE_DIR_ID

    allparts = splitall(abs_path)

    child_item_ids = db.session.query(
        Ancestors.child_id).filter(Ancestors.child_id != Ancestors.parent_id).distinct().all()

    print(f'child_item_ids={child_item_ids}')
    print(f'{allparts[0]}')
    root_item = with_row_locks(db.session.query(Item), of=Item).filter(and_(not_(Item.id.in_(child_item_ids)),
                                                                            Item.name == allparts[0])).first()
    if not root_item:
        print(f'Item {allparts[0]} in path {abs_path} does not exist')
        return False, BASE_DIR_ID
        raise ValueError(
            f'Item {allparts[0]} in path {abs_path} does not exist')

    parent_id = root_item.id

    for item_name in allparts[1:]:
        child_item_ids = db.session.query(Ancestors.child_id).filter(
            Ancestors.parent_id == parent_id).distinct().all()

        item_id = with_row_locks(db.session.query(Item), of=Item).filter(and_(Item.id.in_(child_item_ids),
                                                                              Item.name == item_name)).first()
        if not item_id:
            print(f'Item {item_name} in path {abs_path} does not exist')
            return False, BASE_DIR_ID
            raise ValueError(
                f'Item {item_name} in path {abs_path} does not exist')

        parent_id = item_id.id

    # deepest subdirectory (item) id / current directory id
    return True, parent_id


def list_child_items(parent_id, depth=1):

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


def get_child_item(parent_id, child_name):
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


def add_new_item(name, item_parent_id, data=None):
    try:
        print(f'add new item {name} {item_parent_id}')
        # add to item table
        is_dir = True if data == None else False
        size = len(data) if data else 0
        new_item_id = Item.add_item(
            name=name, size=size, is_dir=is_dir)

        # add to file table
        if data:
            File.add_item(file_id=new_item_id, data=data)

        # add to ancestors table
        Ancestors.add_item(child_id=new_item_id, parent_id=item_parent_id)

        # update item_parent_id size
        parent_item = db.session.query(Item).filter(
            Item.id == item_parent_id).first()

        if parent_item:
            parent_item.update_item_size(parent_item.size + 1)
            # Item(id=parent_item.id,
            #      name=parent_item.name,
            #      created_at=parent_item.created_at,
            #      updated_at=parent_item.updated_at,
            #      size=parent_item.size,
            #      is_dir=parent_item.is_dir).update_item_size(parent_item.size + 1)

            db.session.add(parent_item)

        db.session.commit()

        return new_item_id
    except Exception as e:
        db.session.rollback()
        raise e


def delete_item(id):
    # delete from item table
    Item.delete_item(id)

    # delete from file table
    File.delete_item(id)

    # delete from ancestors table
    Ancestors.delete_item(id)


def move_item(id, new_parent_id):
    item = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == id).first()

    # deleting all relationships of id from ancestors table
    Ancestors.delete_item(id)

    # updating old parent size, updated_at(when item = directory)
    child_parent_rel = with_row_locks(db.session.query(
        Ancestors), of=Ancestors).filter(Ancestors.child == id).first()

    old_parent = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == child_parent_rel.parent_id).first()
    if old_parent.is_dir:
        old_parent.updated_at = datetime.now()

    # updating new parent size, updated_at(when item = directory)
    new_parent = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == new_parent_id).first()
    if new_parent.is_dir:
        new_parent.updated_at = datetime.now()

    if item.is_dir:  # deleted a directory that may contain items
        old_parent.size -= item.is_dir + 1
        new_parent.size += item.is_dir + 1
    else:  # only deleted one file
        old_parent.size -= 1
        new_parent.size += 1

    db.session.add(old_parent)

    # adding new relationships between the item and new parent
    Ancestors.add_item(id, new_parent_id)

    db.session.commit()
