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
from utils.response import InvalidCmdError

# TODO: needs refractoring


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
        Item).filter(Item.id == BASE_DIR_ID), of=Item).first()

    parent_item = root_item
    # if abs_path contains many subdirectories
    for item_name in allparts[1:]:  # skips root
        # get parent folder contents
        child_item_ids = db.session.query(Ancestors.child_id).filter(
            Ancestors.parent_id == parent_item.id).distinct().all()

        # check if item exists in parent folder
        child_item = with_row_locks(db.session.query(Item).filter(and_(Item.id.in_(child_item_ids),
                                                                       Item.name == item_name)), of=Item).first()
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


@provide_db_session
def get_child_item(parent_id, child_name, db=None):
    """
    given parent id and child name -> return child id else None if doesn't exist

    :param parent_id: [description]
    :type parent_id: [type]
    :param child_name: [description]
    :type child_name: [type]

    """
    r = with_row_locks(db.session.query(Ancestors).join(Item, Item.id == Ancestors.child_id).filter(and_(Ancestors.parent_id == parent_id),
                                                                                                    Item.name == child_name)).first()
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
def delete_item_in_folder(id, parent_id, db=None):
    # TODO: this would probably be more efficient
    pass


@provide_db_session
def delete_item(id, db=None):
    # delete from ancestors table
    # NOTE: must delete before item to avoid fk violation
    # returns children items that need to be deleted
    child_item_ids = Ancestors.delete_item(id=id)

    # delete from file table
    # NOTE: must delete before item to avoid fk violation
    with_row_locks(db.session.query(File).filter(
        File.id.in_(child_item_ids+[id])), of=File).delete(synchronize_session=False)

    # delete from item table
    with_row_locks(db.session.query(Item).filter(
        Item.id.in_(child_item_ids+[id])), of=Item).delete(synchronize_session=False)


@provide_db_session
def move_item(id, new_parent_id, db=None):
    # before moving check if item name already exists in parent_folder
    if item_name_exists_in_folder(id, new_parent_id):
        raise InvalidCmdError(
            message="mv: an item with the same name already exists in the dest")
    # cannot move if dest = file and source = folder
    if Item.is_a_dir(id) and not Item.is_a_dir(new_parent_id):
        raise InvalidCmdError(
            message="mv: dest is a file but src is folder")
    # old_parent
    old_parent_id = with_row_locks(db.session.query(Ancestors.parent_id).filter(and_(Ancestors.child_id == id,
                                                                                     Ancestors.depth == 1)), of=Ancestors).first()

    # define subtree as id + all childs of id
    childs = with_row_locks(db.session.query(
        Ancestors).filter(Ancestors.parent_id == id), of=Ancestors).all()
    subtree_ids = [item.child_id for item in childs]
    subtree = with_row_locks(db.session.query(
        Ancestors), of=Ancestors).filter(Ancestors.parent_id.in_(subtree_ids)).all()

    # delete relationships between upper tree of the tree + subtree
    with_row_locks(db.session.query(
        Ancestors).filter(and_(Ancestors.child_id.in_(subtree_ids),
                               not_(Ancestors.parent_id.in_(subtree_ids)))), of=Ancestors).delete(synchronize_session=False)

    # add relationships between (new parent + upper tree of new_parent) + subtree
    new_parent_upper_tree = with_row_locks(db.session.query(Ancestors).filter(
        Ancestors.child_id == new_parent_id), of=Ancestors).all()
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
        Item).filter(Item.id == new_parent_id), of=Item).first()
    old_parent = with_row_locks(db.session.query(Item).filter(
        Item.id == old_parent_id), of=Item).first()

    if new_parent.is_dir:
        new_parent.updated_at = datetime.now()
        new_parent.size += 1

    if old_parent.is_dir:
        old_parent.updated_at = datetime.now()
        old_parent.size -= 1

    db.session.add(new_parent)
    db.session.add(old_parent)


@provide_db_session
def to_abs_path_ids(abs_path, db=None):
    item_names = abs_path.split("/")
    item_names[0] = "/"  # replace '' with '/' to enable querying of root

    item_ids = [0] * len(item_names)
    item_ids[0] = BASE_DIR_ID  # id of root('/') = 0

    for i in range(1, len(item_names)):
        item_name = item_names[i]
        parent_id = item_ids[i-1]

        # get parent folder contents
        child_item_ids = db.session.query(Ancestors.child_id).filter(
            Ancestors.parent_id == parent_id).distinct().all()

        # check if any of the child items have the same name as item_name
        # since item names in same directory are distinct -> should only return at most 1 item
        item = with_row_locks(db.session.query(Item).filter(and_(Item.id.in_(child_item_ids),
                                                                 Item.name == item_name)), of=Item).first()
        # convention used when item doesn't exist in parent
        item_ids[i] = item.id if item else -1

    return (item_names, item_ids)


@provide_db_session
def item_exists_in_folder(item_id, parent_id, db=None):
    if item_id == BASE_DIR_ID:  # don't care about parent_id
        return True

    relationship = with_row_locks(db.session.query(Ancestors).filter(and_(Ancestors.child_id == item_id,
                                                                          Ancestors.parent_id == parent_id,
                                                                          Ancestors.depth == 1)), of=Ancestors).first()
    return True if relationship else False


@provide_db_session
def item_name_exists_in_folder(item_id, parent_id, db=None):
    new_item_name = with_row_locks(db.session.query(
        Item.name).filter(Item.id == item_id), of=Item).first()[0]

    exists_item = with_row_locks(db.session.query(Ancestors, Item).join(
        Item, Item.id == Ancestors.child_id, isouter=True).filter(and_(Ancestors.parent_id == parent_id),
                                                                  Item.name == new_item_name,
                                                                  Ancestors.depth == 1)).first()
    return True if exists_item else False


@provide_db_session
def get_item(item_name, parent_id, db=None):
    # # get parent folder contents
    # child_item_ids = db.session.query(Ancestors.child_id).filter(
    #     Ancestors.parent_id == parent_id).distinct().all()

    # # check if any of the child items have the same name as item_name
    # # since item names in same directory are distinct -> should only return at most 1 item
    # item = with_row_locks(db.session.query(Item), of=Item).filter(and_(Item.id.in_(child_item_ids),
    #                                                                    Item.name == item_name)).first()
    query = db.session.query(Ancestors, Item).filter(
        Ancestors.parent_id == parent_id)
    item = with_row_locks(query.join(Item, Item.id == Ancestors.child_id, isouter=True).filter(
        Item.name == item_name)).first()

    return item[1] if item else None


@provide_db_session
def _resolve_path(item_name_list, item_id_list, begin_indx=1, db=None):
    _item_names = item_name_list[:]
    _item_ids = item_id_list[:]

    # process from begin_indx -> second last arr element
    for i in range(begin_indx, len(_item_names) - 1):
        parent_id = _item_ids[i-1]
        item_name = _item_names[i]
        if item_name == "*":
            # will give at most 1 match if intermediate dirs since unique names in same directory
            # using  parent_id  and child_item_name of item to find a match
            # depth between parent_id and child_item of item == 2:
            # parent -> child (no constraint on item_name)
            # child -> child items (item_name constraint = item_names[i+1])
            child_ids = with_row_locks(db.session.query(Ancestors.child_id).filter(and_(Ancestors.parent_id == parent_id,
                                                                                        Ancestors.depth == 2)
                                                                                   ), of=Ancestors).all()

            ancestors_and_item = with_row_locks(db.session.query(Ancestors, Item).join(Item, Item.id == Ancestors.child_id).filter(and_(Ancestors.depth == 1,
                                                                                                                                        Ancestors.child_id.in_(
                                                                                                                                            child_ids),
                                                                                                                                        Item.name == _item_names[i+1]))).all()
            if len(ancestors_and_item):
                res = []

                for _ancestor, _item in ancestors_and_item:
                    _new_item_names = _item_names[:]
                    _found_item_name = with_row_locks(db.session.query(
                        Item.name).filter(Item.id == _ancestor.parent_id), of=Item).first()
                    _new_item_names[i] = _found_item_name[0]

                    _new_item_ids = _item_ids[:]
                    _new_item_ids[i] = _ancestor.parent_id
                    res.extend(_resolve_path(
                        _new_item_names, _new_item_ids, i+1))

                return res
            else:
                raise InvalidCmdError(
                    'unable to resolve asterisks(*) to a valid path : {}'.format("/".join(_item_names)))
        else:
            item = get_item(item_name=item_name, parent_id=parent_id)

            # convention used when item doesn't exist in parent
            _item_ids[i] = item.id if item else -1

    # process last part of the path

    res = []

    # may yield mutiple items if last item in path = '*'
    # get child items of depth = 1
    if _item_names[-1] == '*':
        query = db.session.query(Ancestors, Item).filter(
            Ancestors.parent_id == _item_ids[-2], Ancestors.depth == 1)
        child_items = query.join(
            Item, Item.id == Ancestors.child_id).all()

        for _, item in child_items:
            _item_names = _item_names[:-1] + [item.name]
            _item_ids = _item_ids[:-1] + [item.id]

            res.append((_item_names, _item_ids))
    else:
        item = get_item(item_name=_item_names[-1], parent_id=_item_ids[-2])

        #  convention used when item doesn't exist in parent
        _item_ids[-1] = item.id if item else -1

        res.append((_item_names, _item_ids))

    return res


def resolve_asterisk_in_abs_path(abs_path, db=None):
    item_names = abs_path.split("/")
    # NOTE: item_names[0] = ''

    item_ids = [0] * len(item_names)
    item_ids[0] = BASE_DIR_ID  # id of root('/') = 0

    res = _resolve_path(item_names, item_ids, 1)
    return res
