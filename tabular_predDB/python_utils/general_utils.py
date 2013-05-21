from timeit import default_timer


class Timer(object):
    def __init__(self, task='action', verbose=True):
        self.task = task
        self.verbose = verbose
        self.timer = default_timer
    def __enter__(self):
        self.start = self.timer()
        return self
    def __exit__(self, *args):
        end = self.timer()
        self.elapsed_secs = end - self.start
        self.elapsed = self.elapsed_secs * 1000 # millisecs
        if self.verbose:
            print '%s took:\t% 7d ms' % (self.task, self.elapsed)

def int_generator(start=0):
    next_i = start
    while True:
        yield next_i
        next_i += 1
