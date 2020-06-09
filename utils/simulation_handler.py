from utils.engines_handler import EnginesHandler
import logging as log
from pathlib import Path
import shutil
import subprocess
import time


class SimulationHandler:
    """ Simulation handler is used to load the engine handlers of different simulation tools, e.g. Abaqus or Pace3D.
    The SimulationHandler loads the specific engine set by using the .add_engine() method. It stores the overall name
    of the simulation, the root path and keeps a listing including all iterations. In this listing symbolic links to
    the connected iteration steps in the different engines are stored. While the universal EngineHandler class handles
    one engine each instance, the SimulationHandler works as a communicator in between the different engines.
    """

    def __init__(self, name):
        """
        Args:
            name (str): specific name of this simulation handler
        """
        self.log = log.getLogger(self.__class__.__name__)

        # Check input parameters
        if not isinstance(name, str):
            raise TypeError(f'Input parameter name must be of type string is {type(engine)}.')
        self.name = name

        self.engines = {}
        self.paths = {}
        self.iterations = []

        self.log.debug(f'Initialized simulation handler. (name: {self.name})')

    def add_iteration_step(self, step_name, copy_previous: bool = False):
        """ Adding an iteration step to the simulation. This method is used to add an iteration into each engine
        simultaneously. It is also possible to add an iteration step into each engine separately, but not with
        this method.

        Args:
            step_name (str): name of the iteration to be added
            copy_previous (bool,optional): set true to make a (deep)copy of the previous step, keeping grid information
                            and values

        Returns:
            Dictionary of steps added to the different engines. Key is engine name, value is added iteration step
        """

        if len(self.engines) == 0:
            raise ValueError(f'Before adding an iteration step, engines must be initialized! Use add_engine().')

        steps = {}

        # Iterate through the initialized engines and add iteration step
        for engine in self.engines.values():
            steps[engine.engine_name] = engine.add_iteration_step(step_name, copy_previous)

        # Append the name of the added iteration step "step_name" to the list of iterations "self.iterations"
        self.iterations.append(step_name)

        return steps

    def clear_old_iterations(self):
        """
        Delete old iterations stored in each EngineHandler object to save memory. The actual and the iteration before
        are not touched. If there are less than two iterations nothing will be changed and False will be returned.

        Returns:
            bool: True on success, else False
        """

        if len(self.iterations) > 2:

            # Iterate through the initialized engines and get iteration step
            for engine in self.engines.values():
                engine.iterations[len(engine.iterations) - 3] = None

            return True

        else:
            self.log.info(f'Only {len(self.iterations)} are available in this instance. clear_old_iterations() needs at'
                          f'least three available iterations.')
            return False

    def get_current_iterations(self):
        """ Get a dictionary of the current iteration step of all engines.

        Returns:
            Dictionary of steps added to the different engines. Key is engine name, value is added iteration step.
        """

        if len(self.iterations) > 0:

            steps = {}

            # Iterate through the initialized engines and get iteration step
            for engine in self.engines.values():
                steps[engine.engine_name] = engine.iterations[len(engine.iterations) - 1]

            return steps

        else:
            raise IndexError(f'No iterations available in this simulation.')

    def get_previous_iterations(self):
        """ Get a dictionary of the previous iteration step of all engines.

        Returns:
            Dictionary of steps added to the different engines. Key is engine name, value is added iteration step
        """

        if len(self.iterations) > 1:

            steps = {}

            # Iterate through the initialized engines and get iteration step
            for engine in self.engines.values():
                steps[engine.engine_name] = engine.iterations[len(engine.iterations) - 2]

            return steps

        else:
            self.log.warning(f'Only one iteration available in this simulation. There is no previous iteration so far. '
                             f'Current iteration returned instead.')
            return self.get_current_iterations()

    def add_engine(self, engine_name):
        """ Add a new engine to the SimulationHandler instance. A new engine will be added by the universal
        EngineHandler class. The initialization by engine_name (e.g. Abaqus) only leads to a new entry in the engine
        listing .engines in this instance. The new instance of EngineHandler has to be initialized by
        EngineHandler.init_engine().

        Args:
            engine_name (str): name of the engine used by the EngineHandler class to identify the engine

        Returns:
            EngineHandler instance of the added engine
        """

        # Check input parameters
        if not isinstance(engine_name, str):
            raise TypeError(f'Input parameter engine_name must be of type string is {type(engine)}.')
        elif len(self.engines) > 0:  # Check if this engine name is already in use
            for key in self.engines.keys():
                if key == engine_name:
                    raise NameError(f'An engine with the given name already exists. ({engine_name})')

        # Initialize new EngineHandler object
        engine = EnginesHandler(engine_name)

        if engine:
            self.engines[engine_name] = engine
            return self.engines[engine_name]

        else:
            raise NameError(f'Error on adding EnginesHandler for {engine_name}.')

    def set_path(self, path_name, path, create_missing=True, cleanup=False):
        """ Set a global path like "root", "output" or "input". With the path_name the kind of path is defined. The
        used path is a string converted to a Path class. The optional parameter create_missing includes the option
        to create the directories as they are not existing. The cleanup parameter can be set, but has only impact on the
        setting of the output directory, to prevent input or root accidentally directory from data loss.

        Args:
            path_name (str): identifier of the path
            path (Path/str): path to directory absolute or relative
            create_missing (bool, optional): set true (default) to create missing folders
            cleanup (bool, optional): set true to clean recursively the added path from included files or directories

        Returns:
            boolean: True on success
        """

        # Check input parameters
        if not isinstance(path_name, str):
            raise TypeError(f'Input parameter path_name must be of type string is {type(engine)}.')

        # Check if path_name is valid
        valid_names = ['output', 'input', 'root']
        if path_name not in valid_names:
            raise NameError(f'{path_name} is not part of {valid_names}')

        try:
            path = Path(path)

            # Check if path is a file or folder
            if path.is_file():
                raise TypeError(f'Given path is a file. Path excepted. ({path})')

            # Check if path exists
            if not path.is_dir():
                # Path does not exist
                if create_missing:
                    if path.mkdir():
                        self.log.debug(f'Path generated successfully. ({path})')
                        self.paths[path_name] = path
                        self.log.info(f'Checked and added path. ({path})')
                        return True

                    else:
                        # Another try
                        if path.mkdir():
                            self.log.debug(f'Path generated successfully. ({path})')
                            self.paths[path_name] = path
                            self.log.info(f'Checked and added path. ({path})')
                            return True
                        else:
                            raise PermissionError(f'Not able to create path. ({path})')
                else:
                    raise NotADirectoryError(f'Path {path} does not exist. If you want to create the path '
                                             f'automatically use the create_missing=True (default) option.')

            else:
                # Path already exists, check if path (only output) is empty
                if not any(path.iterdir()) and path_name == 'output':
                    if not cleanup:
                        self.log.warning(
                            f'Path exists but is not empty. Set option cleanup=True for deleting any files '
                            f'or paths containing this folder. path:{path}')
                    else:
                        if self.output_path_cleanup():
                            return True

                self.paths[path_name] = path
                self.log.debug(f'Checked and added path {path}')

                return True

        except FileNotFoundError as err:
            raise FileNotFoundError(f'Error occurred while setting path {path} as output_path. {err}')

    def set_root_path(self, root_path, create_missing=True):
        """ Set the root path of the simulation and in addition the input and output path by standard values. To create
        possibly missing folders the optional parameter create_missing (default:true) is used. All paths will be saved
        as Path class.

        Args:
            root_path: absolute or relative path to root directory
            create_missing: set true (default) to create missing folders

        Returns:
            boolean: True on success
        """

        input_sub_folder = 'input'
        output_sub_folder = 'output'

        if self.set_path('root', root_path, create_missing, False):
            self.log.debug(f'Root path set for simulation {self.name} to {self.get_root_path()}')

            if self.set_path('output', root_path / output_sub_folder, create_missing, False):
                self.log.debug(f'Output path set for simulation {self.name} to {self.get_output_path()}')

            if self.set_path('input', root_path / input_sub_folder, create_missing, False):
                self.log.debug(f'Input path set for simulation {self.name} to {self.get_input_path()}')
        else:
            raise OSError('Error while setting root path.')

        return True

    def set_output_path(self, path, create_missing=True, cleanup=False):
        return self.set_path('output', path, create_missing, cleanup)

    def set_input_path(self, path, create_missing=True):
        return self.set_path('input', path, create_missing, False)

    def get_root_path(self):
        return Path(self.paths['root'])

    def get_input_path(self):
        return Path(self.paths['input'])

    def get_output_path(self):
        return Path(self.paths['output'])

    def output_path_cleanup(self, recreate_missing=True):
        """
        Cleaning up the output_path means deleting all files and sub folder. Folders saved in engines.self.path
        will be checked and if needed and parameter recreate_missing is set, be recreated. Files will not be checked.

        Args:s
            recreate_missing (bool, optional): If True, probably deleted sub folders will be recreated.

        Returns:
            boolean: True on success
        """

        # Check input parameters
        if not isinstance(recreate_missing, bool):
            raise TypeError(f'Input parameter recreate_missing must be of type bool.')

        path = self.paths['output']

        # Remove and recreate path
        if path.is_dir():
            shutil.rmtree(path)
            time.sleep(0.5)
            path.mkdir()
            self.log.info(f'Cleaned up output path. ({path})')
        else:
            raise FileNotFoundError(f'Output path is not a folder. ({path})')

        if recreate_missing:
            # Check if all paths in self.engines are existing, otherwise create.
            for engine in self.engines.values():
                for name, path in engine.paths.items():
                    if not path.is_dir():
                        time.sleep(0.5)
                        path.mkdir()
                        self.log.info(f'Recreated path(s) for engine {engine.engine_name}: {name} at {path}')

        return True

    def call_subprocess(self, batch_file, cwd_folder):
        """ Calling in the engines created batch files to run the simulations. The batch files will be ran in the
         shell and the progress can be followed up at the run-terminal of python, but is not stored in the log file.

        Args:
            batch_file (str/path): path to the batch-file as Path or String as absolute path
            cwd_folder (str/path: switch to directory before batch file execution

        Returns:
            bool: True on success
        """

        # Check input parameters
        if not isinstance(batch_file, str) and not isinstance(batch_file, Path):
            raise TypeError(f'Input parameter batch_file must be of type string or Path is {type(engine)}.')
        if not isinstance(cwd_folder, str) and not isinstance(cwd_folder, Path):
            raise TypeError(f'Input parameter cwd_folder must be of type string or Path is {type(engine)}.')

        batch_file = Path(batch_file)
        folder = Path(cwd_folder)

        if batch_file.is_file() and folder.is_dir():
            self.log.info(f'Start subprocess in {batch_file} executed in {cwd_folder}')

            subprocess.call(str(batch_file), shell=True, cwd=str(cwd_folder))  # Start simulation in shell

            self.log.debug('End of subprocess')

            return True
        else:
            raise FileNotFoundError(f'Batch-file or execution-folder do not exist. batch-file: ({batch_file}; '
                                    f'execution-folder: {folder})')
