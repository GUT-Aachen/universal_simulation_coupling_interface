import logging as log
from pathlib import Path
import shutil
import time
from engines.abaqus import AbaqusEngine
from engines.pace3d import Pace3dEngine
from utils.iterationStep import IterationStep
import copy


class EnginesHandler:
    """
    The EngineHandler class is used to handle different types of engines, e.g. Abaqus or Pace3D. Each simulation
    software has its specific features which are saved in the specific engine class like AbaqusEngine class. This
    handler class combines the common parts of all the different simulation tools. On initiating the handler class a
    specific engine is loaded into .engine. In this instance the different iteration steps for the specific engine
    are stored in a list (.iterations). Further all paths and files used or needed by the engine are stored in
    .paths/.files. Each instance has its own name, to identify the instance. For each engine used in the simulation
    coupler only one instance of the EngineHandler class is needed.
    """
    def __init__(self, engine):
        self.engine_name = engine
        self.engine = None
        self.iterations = []
        self.paths = {}
        self.files = {}

        self.log = log.getLogger(f'{self.__class__.__name__}:{self.engine_name}')

    def init_engine(self, parameter: dict = None):
        """
        Initialize engine according to self.engine_name. Parameters needed to initialize any engine differ
        on the engine and need to be of type dictionary.

        Args:
            parameter (dict): Dictionary including parameters

        Returns:
            specific engine: for example AbaqusEngine()
        """

        if self.engine:
            self.log.error(f'Engine already initialized: {self.engine}')
            return False

        if parameter is None:
            parameter = {}

        if self.engine_name == 'abaqus':
            if 'input_file' in parameter:
                engine = AbaqusEngine(parameter['input_file'])
            else:
                raise TypeError(f'Missing parameter "input_file" in parameters: {parameter}')

        elif self.engine_name == 'pace3d':
            engine = Pace3dEngine()

        else:
            raise TypeError(f'Engine {self.engine_name} is unknown.')

        self.log.info(f'Engine {self.engine_name} successfully initialized')
        self.engine = engine
        return engine

    def add_iteration_step(self, iteration_name, previous_copy=False, delete_previous_grid=True):
        """ Add an iteration step to this instance of the engine handler.

        Args:
            iteration_name: name of the iteration to be added
            previous_copy (boolean, optional): set true to make a (deep)copy of the previous step, keeping grid
                                                information and values
            delete_previous_grid (boolean, optional): set true to delete grid from previous iteration step to save
                                                        memory

        Returns:
            IterationStep on success
        """

        step_no = len(self.iterations)
        step_name_exists = False

        # Check if the step name given by a input parameter is used for a previous step. The name must be unique. There
        # fore a error is raised, when the name already exists.
        for iterations in self.iterations:
            if iterations.name == iteration_name:
                step_name_exists = True

        if step_name_exists:
            raise NameError(f'Step with the same name ({iteration_name}) already exists.')

        else:
            # Delete grid of previous simulation. This step is only necessary to save systems memory. The grid of the
            # actual step will be kept and only thegrid of the previous step will be deleted. Steps before the previous
            # step are not affected.
            if delete_previous_grid:
                if len(self.iterations) > 1:
                    self.iterations[len(self.iterations) - 2].grid = None

            # If input parameter previous_copy is set a deepcopy of the previous step will be created and only the
            # name and step_no will be changed.
            if previous_copy:
                previous_iteration = self.iterations[len(self.iterations) - 1]
                current_iteration = copy.deepcopy(previous_iteration)
                self.iterations.append(current_iteration)

                previous_iteration_name = previous_iteration.name

                current_iteration.name = iteration_name
                current_iteration.step_no = step_no

                self.log.debug(f'Added copy of previous iteration step "{previous_iteration_name}" with new '
                               f'name "{iteration_name}"')
                return current_iteration
            else:
                self.iterations.append(IterationStep(iteration_name, step_no))
                self.log.debug(f'Added new iteration step: {iteration_name}')
                return self.iterations[step_no]

    def get_curr_iteration_step(self):
        """ Get the current iteration step.

        Returns:
            IterationStep
        """
        if len(self.iterations) > 0:
            return self.iterations[len(self.iterations) - 1]
        else:
            return False

    def path_cleanup(self, path_name, recreate_missing=True):
        """
        Cleaning up the given path means deleting all files and subfolder. Folders saved in self.path will be checked
        and if needed and parameter recreate_missing is set be recreated. No longer existing files in self.files will
        be deleted from dictionary.

        Args:
            path_name (str, path): Dictionary including parameters
            recreate_missing (bool): If True, probably deleted folders will be recreated.

        Returns:
            boolean: true on success
        """
        path = self.get_path(path_name)

        # Check if path is file or folder
        if path.is_file():
            raise TypeError(f'Given path is a file. Expected path.')

        # Remove recursive and optionally recreate folder (see recreate_missing option)
        if path.is_dir():
            shutil.rmtree(path)  # Remove all files and sub folders recursively
            path.mkdir()  # Create dir
            self.log.info(f'Cleaned up path {path}')

        # FIXME Recreate only betroffene folder
        if recreate_missing:
            # Check if all paths in self.path are exist, otherwise create.
            for name, path in self.paths.items():
                if not path.is_dir():
                    time.sleep(0.5)
                    path.mkdir()
                    self.log.info(f'Recreated path for {name} at {path}')

        # Check if all files still exist, otherwise delete from self.files
        remove_names = []
        for name, file in self.files.items():
            if not file.is_file():
                remove_names.append(name)

        for i in range(len(remove_names)):
            self.log.info(f'File {remove_names[i]} no longer available. List entry deleted. '
                          f'{self.files[remove_names[i]]}')
            del(self.files[remove_names[i]])

        return True

    def set_path(self, path_name, path, create_missing=True):
        """
        Save path with given name in self.paths. If parameter create_missing is set to True a path will be created if
        it does not exist. Otherwise existence will be ignored.

        Args:
            path_name (str):  Name of the path for later use
            path (str, path): Path to add as Path or String
            create_missing (bool): If True, probably missing folders will be created

        Returns:
            boolean: true on success
        """
        try:
            path = Path(path)

            if path.is_file():
                self.log.error(f'Given path {path} is a file. Use .set_file() instead.')
                raise TypeError

            if not path.is_dir():
                if create_missing:
                    path.mkdir()

                    if path.is_dir():
                        self.log.debug(f'Path {path_name} generated:{path}')
                        self.paths[path_name] = path
                        self.log.debug(f'Checked and added path {path_name} : {path}')
                        return True

                    else:
                        self.log.error(f'Not able to create path {path_name} : {path}')

                else:
                    self.log.warning(f'Path {path} does not exist.')
                    raise FileNotFoundError

            else:
                self.paths[path_name] = path
                self.log.debug(f'Checked and added path {path_name} : {path}')
                return True

        except FileNotFoundError as err:
            raise FileNotFoundError(f'Error occurred while setting path {path} as {path_name}. {err}')

    def get_path(self, path_name):
        """
        Get path by path_name from self.paths. Returns a Path-object.

        Args:
            path_name (str):  Representing name of the path in this instance

        Returns:
            Path: Path of the path
        """
        try:
            return self.paths[path_name]

        except KeyError as err:
            raise KeyError(f'Error occurred while reading path {path_name}. {err}')

    def set_file(self, file_name, file):
        """
        Save file with given name in self.files.

        Args:
            file_name (str):  Name of the file for later use
            file (str, path): File to add as Path or String

        Returns:
            boolean: true on success
        """
        try:
            file = Path(file)
            if file.is_dir():
                raise IsADirectoryError(f'Given file is a path. Use .set_path() instead.')

            if file.is_file():
                self.files[file_name] = file
                self.log.debug(f'Checked and added file {file_name} : {file}')
                return True
            else:
                raise FileNotFoundError(f'File {file} not found.')

        except FileNotFoundError as err:
            raise FileNotFoundError(f'Error occurred while setting file {file} as {file_name}. {err}')

    def get_file(self, file_name):
        """
        Get file by file_name from self.files. Returns a Path-object.

        Args:
            file_name (str):  Representing name of the file in this instance

        Returns:
            Path: Path to file
        """
        try:
            return self.files[file_name]

        except KeyError as err:
            raise KeyError(f'Error occurred while reading file {file_name}. {err}')
