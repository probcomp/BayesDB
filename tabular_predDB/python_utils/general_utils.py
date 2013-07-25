import itertools
import inspect
from timeit import default_timer
import datetime

class Timer(object):
    def __init__(self, task='action', verbose=True):
        self.task = task
        self.verbose = verbose
        self.timer = default_timer
        self.start = None
    def get_elapsed_secs(self):
        end = self.timer()
        return end - self.start
    def __enter__(self):
        self.start = self.timer()
        return self
    def __exit__(self, *args):
        self.elapsed_secs = self.get_elapsed_secs()
        self.elapsed = self.elapsed_secs * 1000 # millisecs
        if self.verbose:
            print '%s took:\t% 7d ms' % (self.task, self.elapsed)

def int_generator(start=0):
    next_i = start
    while True:
        yield next_i
        next_i += 1

def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = itertools.cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = itertools.cycle(itertools.islice(nexts, pending))

# introspection helpers
def is_obj_method_name(obj, method_name):
    attr = getattr(obj, method_name)
    is_method = inspect.ismethod(attr)
    return is_method
#
def get_method_names(obj):
    is_this_obj_method_name = lambda method_name: \
        is_obj_method_name(obj, method_name)
    #
    this_obj_attrs = dir(obj)
    this_obj_method_names = filter(is_this_obj_method_name, this_obj_attrs)
    return this_obj_method_names
#
def get_method_name_to_args(obj):
    method_names = get_method_names(obj)
    method_name_to_args = dict()
    for method_name in method_names:
        method = obj.__dict__[method_name]
        arg_str_list = inspect.getargspec(method).args[1:]
        method_name_to_args[method_name] = arg_str_list
    return method_name_to_args

def get_getname(name):
    return lambda in_dict: in_dict[name]

def print_ts(in_str):
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print_str = '%s:: %s' % (now_str, in_str)
    print print_str
    
