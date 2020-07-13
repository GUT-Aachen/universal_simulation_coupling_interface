import logging as log
from utils.grid import Grid
from pathlib import Path


class IterationsDict(dict):
    """
    IterationsDict is a modified Dictionary object (dict). It has the additional option to add a new iteration step, by
    setting a iterations name and number.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = log.getLogger(self.__class__.__name__)

    def add_iteration_step(self, iteration_name, step_no=None):
        """
        Adding an additional step into this instance. This step will be added into the dictionary and a IterationStep
        object is initialized. A name for this step (iterations_name) is mandatory and a step number (step_no) can be
        added. If not set, the step number (step_no) will be increased by one/set to the length of the instance.
        The new entry in the instance (dictionary) is stored with iteration_name as key and IterationStep object as
        value.

        Args:
            iteration_name (str): Name of the added step.
            step_no (int, optional): Number of the added step. Default:None

        Returns:
            Added entry of the instance as a dict value.

        """
        if iteration_name in self:
            raise NameError(f'Step with the same name ({iteration_name}) already exists.')
        else:
            if not isinstance(step_no, int):
                step_no = len(self)

            self.log.debug(f'Added new iteration step: {iteration_name}')
            self[iteration_name] = IterationStep(iteration_name, step_no)
            return self[iteration_name]


class IterationStep:
    """
    An IterationStep object combines all information needed to run or collected from a finished simulation step. Those
    are for example a Grid object, file Path object and addition information like name or computing time. These
    IterationStep objects are usually stored in an IterationsDict object.
    """

    def __init__(self, iteration_name: str, step_no: int):
        """

        Args:
            iteration_name (str): Name of the iteration
            step_no (int): Number of the step
        """

        # Check input parameters
        if not isinstance(iteration_name, str):
            raise TypeError(f'Input parameter iteration_name must be of type string.')
        if not isinstance(step_no, int):
            raise TypeError(f'Input parameter step_no must be of type integer.')

        self.grid = Grid()  # Initialize Grid object
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
        # Check input parameters
        if not isinstance(prefix, str):
            raise TypeError(f'Input parameter prefix must be of type string.')

        self.prefix = prefix

    def get_prefix(self):
        return self.prefix

    def set_step_folder(self, parent_folder):
        """
        FUNCTION IS DEPRECATED Use create_step_folder() instead.

        Set sub folder where additional files for this step are stored.

        Args:
            parent_folder (str, Path): Path or string of path of the parent folder

        Returns:
            boolean: true on success
        """
        self.log.warning(f'This function (set_step_folder()) is deprecated. Use create_step_folder() instead.')
        return self.create_step_folder(parent_folder, False)

    def create_step_folder(self, parent_folder, create_if_missing=True):
        """
        Setting and optionally creating sub folder where additional files for this step are stored.

        Args:
            parent_folder (str, Path): Path or string of path of the parent folder
            create_if_missing (bool, optional): Shall the folder created if it does not exist?

        Returns:
            boolean: true on success
        """

        # Check input parameters
        if not isinstance(parent_folder, str) and not isinstance(parent_folder, Path):
            raise TypeError(f'Input parameter parent_folder must be of type string or Path.')
        else:
            parent_folder = Path(parent_folder)

        sub_folder = f'step_{self.name}'

        path = parent_folder / sub_folder

        if not path.is_dir():
            if create_if_missing:
                path.mkdir()
                self.log.debug(f'Sub folder set and created successfully to. ({path})')
            else:
                raise FileNotFoundError(f'Sub folder does not exist and shall not be created. ({path})')
        else:
            self.log.debug(f'Sub folder set successfully, but already exists. ({path})')

        self.path = path
        return path
