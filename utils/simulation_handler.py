from utils.engines_handler import EnginesHandler
import logging as log
from pathlib import Path
import shutil
import subprocess
import time


class SimulationHandler:

    def __init__(self, name):
        self.log = log.getLogger(self.__class__.__name__)

        self.engines = {}
        self.name = name
        self.paths = {}

        self.log.debug(f'Initialized simulation handler for {self.name}')

        self.iterations = []

    def add_iteration_step(self, step_name, copy_previous=False):

        if len(self.engines) == 0:
            self.log.error(f'Before adding an iteration step, engines must be initialized!')
            raise ValueError

        steps = {}

        for engine in self.engines.values():
            steps[engine.engine_name] = engine.add_iteration_step(step_name, copy_previous)

        self.iterations.append(step_name)

        return steps

    def get_current_iterations(self):

        if len(self.iterations) > 0:

            steps = {}

            for engine in self.engines.values():
                steps[engine.engine_name] = engine.iterations[len(engine.iterations) - 1]

            return steps

        else:
            self.log.error(f'No iterations available in this simulation.')
            raise IndexError

    def get_previous_iterations(self):

        if len(self.iterations) > 1:

            steps = {}

            for engine in self.engines.values():
                steps[engine.engine_name] = engine.iterations[len(engine.iterations) - 2]

            return steps

        else:
            self.log.warning(f'Only one iteration available in this simulation. There is no previous iteration so far. '
                           f'Current iteration returned instead.')
            return self.get_current_iterations()

    def add_engine(self, engine_name):
        """"""

        engine = EnginesHandler(engine_name)
        if engine:
            self.engines[engine_name] = engine
            return self.engines[engine_name]

        else:
            self.log.error(f'Error on adding EnginesHandler for {engine_name}.')
            return False

    def set_path(self, path_name, path, create_missing=True, cleanup=False):
        """"""

        # Check if path_name is valid
        valid_names = ['output', 'input', 'root']
        if not path_name in valid_names:
            self.log.error(f'{path_name} is not part of {valid_names}')
            raise NameError

        try:
            path = Path(path)

            # Check if path is a file or folder
            if path.is_file():
                self.log.error(f'Given path is a file. Path empty excepted.')
                raise TypeError

            # Check if path exists
            if not path.is_dir():

                if create_missing:
                    if path.mkdir():
                        self.log.info(f'Path {path} generated.')
                        self.paths[path_name] = path
                        self.log.debug(f'Checked and added output_path {path}')
                        return True

                    else:
                        # Another try
                        if path.mkdir():
                            self.log.info(f'Path {path} generated.')
                            self.paths[path_name] = path
                            self.log.debug(f'Checked and added output_path {path}')
                            return True
                        else:
                            self.log.error(f'Not able to create output_path {path}')
                            raise PermissionError
                else:
                    self.log.error(f'Path {path} does not exist. If you want to create the path automatically use '
                                   f'the create_missing=True (default) option.')
                    raise NotADirectoryError

            else:
                # Check if path is empty
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
            self.log.error(f'Error occured while setting path {path} as output_path. {err}')
            raise FileNotFoundError

    def set_root_path(self, path, create_missing=True):

        input_sub_folder = 'input'
        output_sub_folder = 'output'

        if self.set_path('root', path, create_missing, False):
            self.log.debug(f'Root path set for simulation {self.name} to {self.get_root_path()}')

            if self.set_path('output', path / output_sub_folder, create_missing, False):
                self.log.debug(f'Output path set for simulation {self.name} to {self.get_output_path()}')

            if self.set_path('input', path / input_sub_folder, create_missing, False):
                self.log.debug(f'Input path set for simulation {self.name} to {self.get_input_path()}')
        else:
            self.log.error('Error while setting root path.')
            raise OSError

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
        Cleaning up the output_path means deleting all files and subfolder. Folders saved in engines.self.path
        will be checked and if needed and parameter recreate_missing is set, be recreated. Files will not be checked.

        Args:s
            recreate_missing (bool): If True, probably deleted folders will be recreated.

        Returns:
            boolean: true on success
        """

        path = self.paths['output']

        try:
            if path.is_file():
                self.log.error(f'Given path is a file. Expected path.')
                raise TypeError

            # Remove and recreate path
            if path.is_dir():
                shutil.rmtree(path)
                time.sleep(0.5)
                path.mkdir()
                self.log.info(f'Cleaned up output_path {path}')
            # FIXME Recreate only concerned folder
            if recreate_missing:
                # Check if all paths in self.engines are existing, otherwise create.
                for engine in self.engines.values():
                    for name, path in engine.paths.items():
                        if not path.is_dir():
                            time.sleep(0.5)
                            path.mkdir()
                            self.log.info(f'Recreated path for engine {engine.engine_name}: {name} at {path}')

            return True

        except Exception:
            self.log.error(f'An error occured while cleaning up output_path {path}')
            raise Exception

    def call_subprocess(self, file, cwd_folder):
        self.log.info(f'Start subprocess in {file} executed in {cwd_folder}')

        file = Path(file)
        folder = Path(cwd_folder)
        if file.is_file() and folder.is_dir():
            subprocess.call(str(file), shell=True, cwd=str(cwd_folder))  # Start simulation in shell
            self.log.debug('End of subprocess')
            return True
        else:
            self.log.error(f'Batch-file or execution-folder do not exist. batch-file {file}; execution-folder {folder}')
            return False
