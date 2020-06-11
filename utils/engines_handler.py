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

        # Check input parameters
        if not isinstance(engine, str):
            raise TypeError(f'Input parameter engine must be of type string is {type(engine)}.')

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
            parameter (dict, optional): Dictionary including parameters

        Returns:
            specific engine: for example AbaqusEngine()
        """

        if self.engine:
            self.log.error(f'Engine already initialized: {self.engine}')
            return False

        if not isinstance(parameter, dict) and parameter is not None:
            raise TypeError(f'Input parameter parameter must be of type Dictionary is {type(parameter)}.')

        if parameter is None:
            parameter = {}

        # Initialization of an engine depends on the engine type.
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
            iteration_name (str): name of the iteration to be added
            previous_copy (bool, optional): set true to make a (deep)copy of the previous step, keeping grid
                                                information and values
            delete_previous_grid (bool, optional): set true to delete grid from previous iteration step to save
                                                        memory

        Returns:
            IterationStep on success
        """

        # Check input parameters
        if not isinstance(iteration_name, str):
            raise TypeError(f'Input parameter iteration_name must be of type string is {type(iteration_name)}.')
        if not isinstance(previous_copy, bool):
            raise TypeError(f'Input parameter previous_copy must be of type boolean is {type(previous_copy)}.')
        if not isinstance(delete_previous_grid, bool):
            raise TypeError(f'Input parameter delete_previous_grid must be of type boolean is '
                            f'{type(delete_previous_grid)}.')

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
            # actual step will be kept and only the grid of the previous step will be deleted. Steps before the previous
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
            self.log.warning(f'There is not iteration step to get. First an iteration has to be initialized by '
                             f'add_iteration_step()')
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

        # Check input parameter
        if not isinstance(recreate_missing, bool):
            raise TypeError(f'Input parameter recreate_missing must be of type boolean, is {type(recreate_missing)}.')

        path = self.get_path(path_name)

        # Check if path is file or folder
        if path.is_file():
            raise TypeError(f'Given path is a file. Expected path.')

        # Remove recursive and optionally recreate folder (see recreate_missing option)
        if path.is_dir():
            shutil.rmtree(path)  # Remove all files and sub folders recursively
            path.mkdir()  # Create dir
            self.log.info(f'Cleaned up path {path}')

        if recreate_missing:
            # Check if all paths in self.path are exist, otherwise create.
            for name, path in self.paths.items():
                if name == path_name:
                    if not path.is_dir():
                        time.sleep(0.5)
                        path.mkdir()
                        self.log.info(f'Recreated path for {name} at {path}.')

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

        # Check input parameters
        if not isinstance(path_name, str):
            raise TypeError(f'Input parameter path_name must be of type string, is {type(path_name)}.')
        if not isinstance(path, str) and not isinstance(path, Path):
            raise TypeError(f'Input parameter path must be of type string or Path, is {type(create_missing)}.')
        if not isinstance(create_missing, bool):
            raise TypeError(f'Input parameter create_missing must be of type boolean, is {type(create_missing)}.')

        path = Path(path)

        if path.is_file():
            raise NotADirectoryError(f'Given path {path} is a file. Use .set_file() instead.')

        if not path.is_dir():
            if create_missing:
                path.mkdir()

                if path.is_dir():
                    self.log.debug(f'Path {path_name} generated:{path}')
                    self.paths[path_name] = path
                    self.log.debug(f'Checked and added path {path_name} : {path}')
                    return True

                else:
                    raise OSError(f'Not able to create path {path_name} : {path}')

            else:
                raise NotADirectoryError(f'Path {path} does not exist.')

        else:
            self.paths[path_name] = path
            self.log.debug(f'Checked and added path {path_name} : {path}')
            return True

    def get_path(self, path_name):
        """
        Get path by path_name from self.paths. Returns a Path-object.

        Args:
            path_name (str):  Representing name of the path in this instance

        Returns:
            Path: Path of the path
        """

        # Check input parameters
        if not isinstance(path_name, str):
            raise TypeError(f'Input parameter path_name must be of type string, is {type(path_name)}.')
        else:
            # Check if path_name is part of self.paths
            path_name_exists = False

            for key in self.paths.keys():
                if key == path_name:
                    path_name_exists = True

            if not path_name_exists:
                raise KeyError(f'Path name does not exist. ({path_name})')

        return self.paths[path_name]

    def set_file(self, file_name, file):
        """
        Save file with given name in self.files.

        Args:
            file_name (str):  Name of the file for later use
            file (str/path): File to add as Path or String

        Returns:
            boolean: true on success
        """

        # Check input parameters
        if not isinstance(file_name, str):
            raise TypeError(f'Input parameter file_name must be of type string, is {type(file_name)}.')
        if not isinstance(file, str) and not isinstance(file, Path):
            raise TypeError(f'Input parameter file must be of type string or Path, is {type(file_name)}.')

        file = Path(file)
        if file.is_dir():
            raise IsADirectoryError(f'Given file is a directory. Use .set_path() instead.')

        if file.is_file():
            self.files[file_name] = file
            self.log.debug(f'Checked and added file {file_name} : {file}')
            return True
        else:
            raise FileNotFoundError(f'File not found. ({file})')

    def get_file(self, file_name):
        """
        Get file by file_name from self.files. Returns a Path-object.

        Args:
            file_name (str):  Representing name of the file in this instance

        Returns:
            Path: Path to file
        """

        # Check input parameters
        if not isinstance(file_name, str):
            raise TypeError(f'Input parameter file_name must be of type string, is {type(file_name)}.')
        else:
            # Check if path_name is part of self.paths
            file_name_exists = False

            for key in self.files.keys():
                if key == file_name:
                    file_name_exists = True

            if not file_name_exists:
                raise KeyError(f'Path name does not exist. ({file_name})')

        return self.files[file_name]
