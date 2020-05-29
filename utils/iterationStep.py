import logging as log
from utils.grid import Grid
from pathlib import Path


class IterationsDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log.getLogger(self.__class__.__name__)

    def add_iteration_step(self, iteration_name, step_no=None):
        if iteration_name in self:
            raise NameError(f'Step with the same name ({iteration_name}) already exists.')
        else:
            if not isinstance(step_no, int):
                step_no = len(self)

            self.log.debug(f'Added new iteration step: {iteration_name}')
            self[iteration_name] = IterationStep(iteration_name, step_no)
            return self[iteration_name]


class IterationStep:
    def __init__(self, iteration_name, step_no):

        self.grid = Grid()
        self.name = iteration_name
        self.prefix = None
        self.computing_time = None
        self.time = None
        self.path = Path()
        self.step_no = step_no
        self.log = log.getLogger(f'{self.__class__.__name__}:{step_no}_{iteration_name}')

        self.log.debug(f'New iteration step initialized. name={self.name}; step_no={self.step_no}')

    def get_path(self):
        return self.path

    def get_grid(self):
        return self.grid

    def __str__(self):
        return f'name={self.name}; no={self.step_no}; grid-size={len(self.grid)} '

    __repr__ = __str__

    def set_prefix(self, prefix: str):
        self.prefix = prefix

    def get_prefix(self):
        return self.prefix

    def set_step_folder(self, parent_folder):
        """
        Set sub folder where additional files for this step are stored.

        Args:
            parent_folder (str, Path): Path or string of path of the parent folder

        Returns:
            boolean: true on success
        """
        parent_folder = Path(parent_folder)

        sub_folder = f'step_{self.name}'

        path = parent_folder / sub_folder

        self.path = path

        if not path.is_dir():
            self.log.warning(f'Subfolder does not exist. {path}')
            return path

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
            raise FileNotFoundError(f'Subfolder does not exist and can not be created. {path}')
