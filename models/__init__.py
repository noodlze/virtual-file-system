from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def with_row_locks(query, **kwargs):
    """
    Apply with_for_update to an SQLAlchemy query, if row level locking is in use.

    :param query: An SQLAlchemy Query object
    :param **kwargs: Extra kwargs to pass to with_for_update (of, nowait, skip_locked, etc)
    :return: updated query
    """
    return query.with_for_update(**kwargs)
