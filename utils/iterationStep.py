import logging as log
from utils.grid import Grid
from pathlib import Path


class IterationsDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log.getLogger(self.__class__.__name__)

    def add_iteration_step(self, iteration_name, step_no=None):
        if iteration_name in self:
            self.log.error(f'Step with the same name ({iteration_name}) already exists.')
            return 0
        else:
            if not isinstance(step_no, int):
                step_no = len(self)

            self[iteration_name] = IterationStep(iteration_name, step_no)
            return self[iteration_name]


class IterationStep:
    def __init__(self, iteration_name, step_no):
        self.log = log.getLogger(self.__class__.__name__)
        self.grid = Grid()
        self.name = iteration_name
        self.computing_time = None
        self.time = None
        self.path = Path()
        self.step_no = step_no
        self.log.debug(f'New iteration step initialized. name={self.name}; step_no={self.step_no}')

    def get_path(self):
        return self.path

    @property
    def get_name(self):
        return self.name

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

    def create_step_folder(self, parent_folder):
        """
        Creating subfolder where additional files for this step are stored.

        Args:
            parent_folder (str, Path): Path or string of path of the parent folder

        Returns:
            boolean: true on success
        """
        parent_folder = Path(parent_folder)

        sub_folder = f'step_{self.name}'

        path = parent_folder / sub_folder

        if not path.is_dir():
            path.mkdir()
            self.path = path
            return path
        if not path.is_dir():
            self.log.error(f'Subfolder does not exist and can not be created. {path}')
            raise FileNotFoundError

