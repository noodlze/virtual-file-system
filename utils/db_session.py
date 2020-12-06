from functools import wraps

# a provide db session that imports from app the initiated db in the wrapper func to avoid circular import


def provide_db_session(func):
    """
    Function decorator that provides a  db session if it isn't provided.
    db session is imported from app.

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        from app import db  # avoids circular imports
        return func(db=db, *args, **kwargs)

    return wrapper
