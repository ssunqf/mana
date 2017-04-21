from decorator import decorator
import time
import frozendict
def memoize_with_expiry(expiry_time=0, num_args=None):
    def _memoize_with_expiry(func, *args, **kwargs):
        func._cache = {}
        mem_args = args[:num_args]
        if kwargs:
            key = mem_args, frozenset(kwargs.iteritems())
        else:
            if type(mem_args[0]) == dict:
                key = frozendict.frozendict(mem_args[0])
            else:
                key = mem_args
        if key in func._cache:
            result, timestamp = func._cache[key]
            # Check the age.
            age = time.time() - timestamp
            if not expiry_time or age < expiry_time:
                return result
        result = func(*args, **kwargs)
        func._cache[key] = (result, time.time())
        return result
    return decorator(_memoize_with_expiry)

