class calculate_once(object):
    """
    Calculates the function result on first call. Afterwards it replies with
    previously calculated value.

    Internally, it replaces itself with the result.

    See:
    http://stackoverflow.com/questions/3012421/python-lazy-property-decorator
    """

    def __init__(self, fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)
        return value
