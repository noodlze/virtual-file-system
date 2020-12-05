from const import BASE_DIR_ID
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
from models import with_row_locks


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


def validate_new_item_name(item_name, parent_id, db):
    same_folder_items = db.session.query(Ancestors).join(
        Item, Item.id == Ancestors.child_id).filter(Ancestors.parent_id == parent_id).distinct().all()

    if item_name in [item.name for item in same_folder_items]:
        return False
    return True


def item_exists(abs_path, db, check_is_dir=False):
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
    for item_name in allparts[1:]: # skips root
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


def list_child_items(parent_id, db, depth=1):

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


def get_child_item(parent_id, child_name, db):
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


def add_new_item(name, item_parent_id, db, data=None):
    try:
        print(f'add new item {name} {item_parent_id}')
        # add to item table
        is_dir = True if data == None else False
        size = len(data) if data else 0
        new_item_id = Item.add_item(db=db,
                                    name=name, size=size, is_dir=is_dir)

        # add to file table
        if data:
            File.add_item(db=db, file_id=new_item_id, data=data)

        # add to ancestors table
        Ancestors.add_item(db=db, child_id=new_item_id,
                           parent_id=item_parent_id)

        # update item_parent_id size
        parent_item = db.session.query(Item).filter(
            Item.id == item_parent_id).first()

        if parent_item:
            parent_item.update_item_size(size=parent_item.size + 1, db=db)
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


def delete_item(id, db):
    # delete from ancestors table
    # NOTE: must delete before item to avoid fk violation
    # returns children items that need to be deleted
    child_item_ids = Ancestors.delete_item(id=id, db=db)

    # delete from file table
    # NOTE: must delete before item to avoid fk violation
    with_row_locks(db.session.query(File), of=File).filter(
        File.id.in_(child_item_ids+[id])).delete(synchronize_session=False)

    # delete from item table
    with_row_locks(db.session.query(Item), of=Item).filter(
        Item.id.in_(child_item_ids+[id])).delete(synchronize_session=False)

    db.session.commit()


def move_item(id, new_parent_id, db):
    print("move item id={}->new_parent_id={}".format(id, new_parent_id))

    item = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == id).first()

    # if directory moving all directory contents to new destination too
    # identify the relationships we would need to add between item (unchanged item id) and new_parent item
    select_child_ids = with_row_locks(
        db.session.query(Ancestors), of=Ancestors).filter(and_(Ancestors.parent_id == id, Ancestors.child_id != id)).all()
    print("find child ids conds include Ancestors.parent_id={}, ancestors.child_id !={}".format(id, id))
    # add new rows with update parent_id -> new parent_id
    new_childs = []
    for c in select_child_ids:
        print("child= parent_id={},child_id={},depth={},rank={}".format(
            c.parent_id, c.child_id, c.depth, c.rank))
        new_c = Ancestors(parent_id=new_parent_id,
                          child_id=c.child_id,
                          depth=c.depth + 1,
                          rank=f'{new_parent_id},' + c.rank.split(",", maxsplit=1)[1])
        old_c_new = Ancestors(parent_id=c.parent_id,
                              child_id=c.child_id, depth=c.depth, rank=c.rank)  # also add the same parent child rel as a new obj
        print("new child: parent_id={},child_id={},depth={},rank={}".format(
            new_c.parent_id, new_c.child_id, new_c.depth, new_c.rank))
        print("new child: parent_id={},child_id={},depth={},rank={}".format(
            new_c.parent_id, new_c.child_id, new_c.depth, new_c.rank))
        new_childs.append(new_c)
        new_childs.append(old_c_new)

    # deleting all relationships of id from ancestors table
    # do not delete subtree, since we are not changing the item id(folder) on move
    Ancestors.delete_item(id=id, db=db, subtree=True)

    db.session.commit()

    # item id has not changed -> we don't want ancestors.delete_item call above to delete these
    # add new rows for subtree relationships
    print("adding new child ids=", new_childs)
    db.session.add_all(new_childs)

    # updating new parent size, updated_at(when item = directory)
    new_parent = with_row_locks(db.session.query(
        Item), of=Item).filter(Item.id == new_parent_id).first()

    if new_parent.is_dir:
        new_parent.updated_at = datetime.now()

    if item.is_dir:  # deleted a directory that may contain items
        new_parent.size += item.is_dir + 1
    else:  # only deleted one file
        new_parent.size += 1

    # adding new relationships between the item and new parent
    # queries only using parent_id -> should not affect existing rows that have item id as parent_id/child_id
    Ancestors.add_item(child_id=id, parent_id=new_parent_id, db=db)

    db.session.commit()
