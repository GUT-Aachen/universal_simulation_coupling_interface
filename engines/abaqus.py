import logging as log
import numpy
from pathlib import Path, PurePath
from utils.grid import Grid
import os


class AbaqusEngine:
    """
    This is a class to handle a Simulia Abaqus input file. It is possible to extract information from the input file
    and to modify/create a new input file.
    """

    def __init__(self, input_file):
        """

        Args:
            input_file: Complete path to the input file as String.
        """
        self.log = log.getLogger(self.__class__.__name__)

        self.input_file = Path(input_file)
        if not self.input_file.is_file():
            raise FileNotFoundError
        if not self.input_file.suffix == '.inp':
            self.log.error(f'Expected an Simulia Abaqus Inputfile with .inp suffix instead of {self.input_file.suffix}')
            raise FileNotFoundError

        # Read input file and save in an array
        self.data = self.input_file.read_text().split('\n')

        self.node_set = {}
        self.paths = {'output': Path(), 'scratch': Path()}

    def __str__(self):
        return self.input_file.name

    def get_part_names(self):
        """
        Searches the input file for all parts.

        Returns: List of parts
        """

        parts = [line[12:] for line in self.data if '*Part, name=' in line]
        return parts

    def get_instance_names(self):
        """
        Searches the input file for all instances assembled from parts. A dictionary containing the instance name
        and the corresponding part name will be returned.

        Returns: Dictionary of all instances like {instance-name : part-name}

        """

        instances = {}
        instances_arr = [line.split(', ')[1:3] for line in self.data if '*Instance, name=' in line]

        for arr in instances_arr:
            key = arr[0][5:]
            value = arr[1][5:]
            instances[key] = value

        return instances

    def get_nodes(self, object_name):
        """ Function to create an listing consisting of dictionary for each found node, containing node number and
            the corresponding coordinates. The name of the part one want to extract the node-coordinates must be passed.
            The part name is not case sensitive! If parts are independent and meshed at the assembly, then the
            name of the assembly must be set as part_name input parameter.

         Parameters:
            object_name (String): Name of the part/assembly

        Returns:
            dict: Containing nodes and corresponding coordinates for each node in part_name {x_coordinate, y_coordinate,
             z_coordinate, node_number}
        """

        try:

            # Coordinates of nodes can be stored in part or in assembly therefore two search strings
            # (case insensitive) have to be created.
            part_string = '*Part, name=' + object_name
            part_string = part_string.lower()
            assembly_string = '*Instance, name=' + object_name
            assembly_string = assembly_string.lower()

            # Variable set to True when node information have been found.
            read_coordinates = False

            # Initialize empty list for collecting dictionarys.
            node_list = []

            # Check each line of input file
            for line in self.data:
                line_string = line.strip().lower()

                # If read_coordinates is True and *Element was found in the actual line, the listing of
                # coordinates ended.
                if '*Element,' in line:
                    if read_coordinates:
                        self.log.debug('Found end of part/assembly.')
                        break

                # True if the coordinates are stored in a part.
                if part_string == line_string:
                    self.log.info(f'Found nodes in parts at "{line_string}". Start reading coordinates of nodes '
                                  f'for this part.')
                    read_coordinates = True
                    continue

                # True if the coordinates are stored in the assembly.
                if assembly_string == line_string[:assembly_string.__len__()]:
                    self.log.info(f'Found nodes in assembly at "{line_string}". Start reading coordinates '
                                  f'of nodes for this part.')
                    read_coordinates = True
                    continue

                # If beginning of coordination listing is found, the coordinates are going to be extracted from
                # each line and appended into an earlier initialized array. It must be checked if the line contains
                # x/y/z or only x/y coordinates.
                if read_coordinates:
                    try:
                        line_array = numpy.fromstring(line, dtype=float, sep=',')

                        node = line_array[0]
                        x = line_array[1]
                        y = line_array[2]
                        z = 0

                        if len(line_array) == 4:
                            z = line_array[3]

                        node_dict = {'node_number': int(node), 'x_coordinate': float(x), 'y_coordinate': float(y),
                                     'z_coordinate': float(z)}

                        node_list.append(node_dict)

                    except Exception as err:
                        self.log.warning(f'An error occured while reading coordinates for nodes in line '
                                         f'{line_string}. Error: {str(err)}')

            self.log.info('Added %s nodes with x/y/z-coordinates', len(node_list))

            if not len(node_list) == 0:
                return node_list

            else:
                self.log.error('No nodes found for part: %s. Abort!', object_name)
                exit()

        except Exception as err:
            self.log.error(str(err))
            return 0

    def create_node_set_all_list(self, set_work_name, instance_name):
        """ Function to create a dictionary consisting of all node number and abaqus node set combinations. An entry
            of the the dictionary looks, due to instance_name = 'Part-1', for example like this:
                (234: *Nset, nset = node-234, internal, instance = Part-1 \n 234).
            It will be checked if the given instance_name exists in the input file.

             Parameters:
                instance_name: name of the instance of a part
                set_work_name: Name to load/save the set in instance
            Returns:
                dictionary{node_no: node_set}
            """

        # Check if assembly_name is part of input file
        instances_dict = self.get_instance_names()
        if instance_name not in instances_dict:
            self.log.error(f'Given instance {instance_name} is not part of the instances in the input file: '
                           f'{instances_dict}')
            return 0

        # Check if the set_work_name exists in instance
        if set_work_name in self.node_set:
            node_set_names_dict = self.node_set[set_work_name]['set_names']
        else:
            self.log.error(f'Set_work_name {set_work_name} not found in {self.node_set.keys()}')
            return 0

        node_set_dict = {}

        try:
            # Every node gets its own node set as shown below:
            # *Nset, nset = node-234, internal, instance = Part-1
            # 234

            for node, name in node_set_names_dict.items():
                nset_string = '*Nset, nset=' + name + ', instance=' + instance_name + '\n' + str(node) + ','
                node_set_dict[int(node)] = nset_string

            self.node_set[set_work_name] = {'sets': node_set_dict}
            self.log.debug(f'Node sets created and saved successfully in .node_set[{set_work_name}][sets]')

            return node_set_dict

        except Exception as err:
            self.log.error(str(err))
            return 0

    def create_node_set_names(self, set_work_name, grid):
        """ Function to create a dictionary consisting of all node number and abaqus node set names. An entry of the
                the dictionary looks for example like this: (234: node-234).

             Parameters:
                set_work_name: Name to save the set in instance
                grid (Grid): A grid of the class Grid containing all node numbers


            Returns:
                dictionary{node_no: node_set_name}
            """

        if isinstance(grid, Grid):
            try:
                node_set_names_dict = {}

                # Every node gets its own node set like: node-234
                for node_number in grid.nodes.keys():
                    node_set = 'node-' + str(node_number)
                    node_set_names_dict[node_number] = node_set

                self.node_set[set_work_name] = {'set_names': node_set_names_dict}
                self.log.debug(f'Node set names created and saved successfully in .node_set['
                               f'{set_work_name}][set_names]')

                return node_set_names_dict

            except Exception as err:
                self.log.error(str(err))
                return 0

        else:
            self.log.error(f'Grid expected but {grid} arrived.')
            return 0

    def create_boundary_condition(self, set_work_name, node_values_dict, bc_1_name, bc_2_name=0):
        """ Function to create a dictionary consisting of all node number and abaqus boundary conditions. An
            entry of the the dictionary looks, due to bc1 = 8, for example like this: (node-234, 8, 8, 123456).
            If the second boundary condition is not set, the bc1 will be used twice, according to Abaqus manual.

             Parameters:
                set_work_name: Name to save the set in instance
                node_values_dict (dict): dictionary consisting of {node_number: boundary condition values}
                bc_1_name: first boundary condition number, according to Abaqus manual
                bc_2_name: second boundary condition number, according to Abaqus manual (optional)

            Returns:
                bc_dict
            """

        # Check if the set_work_name exists in instance
        if set_work_name in self.node_set:
            node_set_names_dict = self.node_set[set_work_name]['set_names']
        else:
            self.log.error(f'Set_work_name {set_work_name} not found in {self.node_set.keys()}')
            return 0

        # If only one boundary condition is given, the second must fit the first one, according to Abaqus manual
        if bc_2_name == 0:
            bc_2_name = bc_1_name

        bc_dict = {}

        # Check if length of all node_numbers given in node_values_dict have a corresponding node sets
        for node_number in node_values_dict:
            if node_number not in node_set_names_dict.keys():
                self.log.error(f'Node {node_number} not found in node sets in .node_set[{set_work_name}][set_names]')
                return 0

        try:
            # Every node gets its own boundary condition as shown below:
            # node-1, 8, 8, 123456
            for node_number, value in node_values_dict.items():

                bc_str = f'{node_set_names_dict[node_number]}, {bc_1_name}, {bc_2_name}, {value}'
                bc_dict[node_number] = bc_str

            self.log.debug(f'Boundary conditions created and saved successfully in .node_set[{set_work_name}]'
                           f'[boundary_conditions].')

            self.node_set[set_work_name]['boundary_conditions'] = bc_dict
            return bc_dict

        except Exception as err:
            self.log.error(str(err))
            return 0

    def write_input_file(self):  # TODO
        return 0

    def set_path(self, path_name, path):
        # Check if given path_name is valid
        if path_name not in self.paths:
            log.error(f'Given path_name ({path_name}) is not part of {self.paths}')
            return False

        try:
            path = Path(path)

            if path.is_dir():
                self.paths[path_name] = path
            else:
                path.mkdir()
                self.paths[path_name] = path

            self.log.debug(f'Output path set successfully to {self.paths[path_name]}')
            return True

        except Exception as err:
            self.log.error(str(err))
            return False

    def write_bash_file(self, input_file_path: str, user_subroutine_path: str = None, use_scratch_path: bool = False,
                        additional_parameters: str = None, old_job_name:str = None):
        """ Function to create bash file, depending on the subsystem (windows or linux) to execute Abaqus
            simulation in console.

         Parameters:
            input_file_path (str): Input filename including path
            user_subroutine_path (str): User subroutine filename including path (optional)
            use_scratch_path (bool): Shall a scratch folder be used. Folder has to be defined via function
            .set_path('scratch') (optional)
            old_job_name (str): name of the old job (optional)
            additional_parameters (str): Additional parameters to be used for the execution of the simulation (optional)

        Returns:
            bash_file_name (String)
        """

        # Check if output path is set
        if not self.paths['output'].is_dir():
            self.log.error(f'Output path must be set first via function .set_path("output", str)')
            return False

        if os.name == 'nt':
            self.log.debug('Running on a windows system. Creating windows bash file.')
            try:
                input_file = Path(input_file_path)
                if not input_file.is_file():
                    self.log.error(f'Set input file {input_file} does not exist.')
                    return False

                if user_subroutine_path:
                    user_subroutine_file = Path(user_subroutine_path)
                    if not user_subroutine_file.is_file():
                        self.log.error(f'Set input file {user_subroutine_file} does not exist.')
                        return False

                # Create job name from input file'
                job_name = input_file.name[:-len(input_file.suffix)]
                bash_file = self.paths['output'] / f'{job_name}.bat'

                # Create the command line for the bash file according to given function input parameters.
                cmd_string = f'call abaqus job={job_name} input={input_file}'

                # Check if oldjob parameter is given and add parameter to command line
                if old_job_name:
                    cmd_string = f'{cmd_string} oldjob={old_job_name}'

                # Add user subroutine to command line
                if user_subroutine_path:
                    cmd_string = f'{cmd_string} user={user_subroutine_path}'

                # Check if scratch parameter is given and add parameter to command line
                if use_scratch_path:
                    if not self.paths['scratch'].is_dir():
                        self.log.error(f'Scratch path must be assigned first via function .set_path("scratch", str)')
                        return False
                    cmd_string = f'{cmd_string} scratch={self.paths["scratch"]}'

                # Add additional parameters to command line
                if additional_parameters:
                    cmd_string = f'{cmd_string} interactive {additional_parameters}'
                else:
                    cmd_string = f'{cmd_string} interactive'

                self.log.debug(f'Created bash file with following content: \n {cmd_string}')

                # Write bash file
                bash_file.write_text(cmd_string)

                self.log.info(f'Bash file created successfully and saved at {bash_file}')
                return bash_file

            except Exception as err:
                self.log.error(str(err))
                return False
        elif os.name == 'posix':
            self.log.error('Batch file builder for Unix not implemented yet.')
        else:
            self.log.error('Using unknown system. No batch file builder available.')

    def preprocessing(self):  # TODO
        return 0

    def postprocessing(self):  # TODO
        return 0