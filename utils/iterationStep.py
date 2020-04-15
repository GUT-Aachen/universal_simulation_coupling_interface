import logging as log
from utils.grid import Grid


class IterationsDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log.getLogger(self.__class__.__name__)

    def add_iteration_step(self, iteration_name):
        if iteration_name in self:
            self.log.error(f'Step with the same name ({iteration_name}) already exists.')
            return 0
        else:
            self[iteration_name] = IterationStep(iteration_name)
            return self[iteration_name]


class IterationStep:
    def __init__(self, iteration_name):
        self.log = log.getLogger(self.__class__.__name__)
        self.grid = Grid()
        self.name = iteration_name
        self.computing_time = None
        self.time = None

    @property
    def get_grid(self):
        return self.grid

    @property
    def time(self):
        return self.time

    @property
    def computing_time(self):
        return self.computing_time

    def __str__(self):
        return f'name={self.name} grid-size={len(self.grid)} '

    __repr__ = __str__

    @time.setter
    def time(self, value):
        self._time = value

    @computing_time.setter
    def computing_time(self, value):
        self._computing_time = value
