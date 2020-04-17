import logging as log
from pathlib import Path
from utils.iterationStep import IterationsDict
import shutil
import time
from engines.abaqus import AbaqusEngine
from engines.pace3d import Pace3dEngine
import subprocess


class EnginesHandler:

    def __init__(self, engine):
        self.log = log.getLogger(self.__class__.__name__)

        self.engine_name = engine
        self.engine = None
        self.iterations = IterationsDict()
        self.paths = {}
        self.files = {}

    def init_engine(self, parameter: dict = {}):
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

        if self.engine_name == 'abaqus':
            if 'input_file' in parameter:
                engine = AbaqusEngine(parameter['input_file'])
            else:
                self.log.error(f'Missing parameter "input_file" in parameters: {parameter}')
                raise TypeError

        elif self.engine_name == 'pace3d':
            engine = Pace3dEngine()

        else:
            self.log.error(f'Engine {self.engine_name} is unknown.')
            raise TypeError

        self.log.info(f'Engine {self.engine_name} successfully initialized')
        self.engine = engine
        return engine

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

        if path.is_file():
            self.log.error(f'Given path is a file. Expected path.')
            raise TypeError

        # Remove and recreate path
        if path.is_dir():
            shutil.rmtree(path)
            time.sleep(0.5)
            path.mkdir()
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
                self.log.error(f'Given path is a file. Use .set_file() instead.')
                raise TypeError

            if not path.is_dir():

                if create_missing:
                    if path.mkdir():
                        self.log.info(f'Path {path} generated.')
                        self.paths[path_name] = path
                        self.log.debug(f'Checked and added path {path}')
                        return True

                    else:
                        # Another try
                        if path.mkdir():
                            self.log.info(f'Path {path} generated.')
                            self.paths[path_name] = path
                            self.log.debug(f'Checked and added path {path}')
                            return True
                        else:
                            # Another try
                            self.log.error(f'Not able to create path {path}')
                else:
                    self.log.warning(f'Path {path} does not exist.')
                    raise FileNotFoundError

            else:
                self.paths[path_name] = path
                self.log.debug(f'Checked and added path {path}')
                return True

        except FileNotFoundError as err:
            self.log.error(f'Error occured while setting path {path} as {path_name}. {err}')
            raise FileNotFoundError

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
            self.log.error(f'Error occurred while reading path {path_name}. {err}')
            raise KeyError

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
                self.log.error(f'Given file is a path. Use .set_path() instead.')
                raise IsADirectoryError

            if file.is_file():
                self.files[file_name] = file
                self.log.debug(f'Checked and added file {file}')
                return True
            else:
                self.log.error(f'File {file} not found.')
                raise FileNotFoundError

        except FileNotFoundError as err:
            self.log.error(f'Error occurred while setting file {file} as {file_name}. {err}')
            raise FileNotFoundError

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
            self.log.error(f'Error occured while reading file {file_name}. {err}')
            return False

    def call_subprocess(self, bash_file, cwd_folder):
        self.log.debug(f'Start simulation with {bash_file}')
        subprocess.call(bash_file, shell=True, cwd=cwd_folder)
        self.log.debug('End simulation')
        return True
