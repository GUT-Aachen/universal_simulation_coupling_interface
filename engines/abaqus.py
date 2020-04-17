import logging as log
import numpy
from pathlib import Path
from utils.grid import Grid
import os
import csv


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
            self.log.error(f'Cannot find input_file {input_file}')
            raise FileNotFoundError
        if not self.input_file.suffix == '.inp':
            self.log.error(f'Expected an Simulia Abaqus Inputfile with .inp suffix instead of {self.input_file.suffix}')
            raise FileNotFoundError

        # Read input file and save in an array
        self.data = self.input_file.read_text().split('\n')

        # Set input file placeholder
        self.placeholder_input_file = {'restart': '** restart_point_python_placeholder',
                                       'nset': '** Nset_python_fill_in_placeholder',
                                       'bc': '** bc_python_fill_in_placeholder'}

        # Check if placeholders are present in input file
        for text in self.placeholder_input_file.values():
            if text not in self.data:
                log.warning(f'To modify or create additional input files minor placeholders have to be set in the '
                            f'initial input file. Otherwise errors will occure. The following placeholder is'
                            f' missing: {text}')

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

            self.node_set[set_work_name]['sets'] = node_set_dict
            self.log.debug(f'Node sets created and stored successfully in .node_set[{set_work_name}][sets]')

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

                if set_work_name not in self.node_set:
                    self.node_set[set_work_name] = {}

                self.node_set[set_work_name]['set_names'] = node_set_names_dict
                self.log.debug(f'Node set names created and saved successfully in .node_set'
                               f'[{set_work_name}][set_names]')

                return node_set_names_dict

            except Exception as err:
                self.log.error(str(err))
                return 0

        else:
            self.log.error(f'Grid expected but {grid} arrived.')
            return 0

    def create_boundary_condition(self, set_work_name: str, node_values_dict: dict, bc_1_name: int, bc_2_name: int = 0):
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
            if 'set_names' in self.node_set[set_work_name]:
                node_set_names_dict = self.node_set[set_work_name]['set_names']
            else:
                self.log.error(f'"set_names" not found in {self.node_set[set_work_name].keys()}')
                return 0
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

            self.log.debug(f'Boundary conditions created and stored successfully in .node_set[{set_work_name}]'
                           f'[boundary_conditions].')

            self.node_set[set_work_name]['boundary_conditions'] = bc_dict
            return bc_dict

        except Exception as err:
            self.log.error(str(err))
            return 0

    def write_input_file(self, set_work_name: str, job_name: str, path):
        """
        This function modifies the initial input file and saves it in instances output folder with the name
         'job_name'.inp. To modify the input file, spcific placeholders have to be placed in the initial input
         file.

        Args:
            set_work_name (str): Name to load/save the set in instance
            job_name (str): Name of the Abaqus job
            path (Path):  Where to save input-file

        Returns:
            written input file (path)
        """

        if set_work_name in self.node_set:
            if 'sets' in self.node_set[set_work_name] and 'boundary_conditions' in self.node_set[set_work_name]:
                node_sets_dict = self.node_set[set_work_name]['sets']
                bc_dict = self.node_set[set_work_name]['boundary_conditions']
            else:
                self.log.error(f'Boundary conditions and/or node sets are not created in '
                               f'set_work_name {set_work_name}. Use .create_boundary_condition() first.')
                return 0
        else:
            self.log.error(f'Set_work_name {set_work_name} not found in {self.node_set.keys()}')
            return 0

        try:
            input_file = path / f'{job_name}.inp'

            input_file_text = []

            for line in self.data:

                if '** Nset_python_fill_in_placeholder' in line:
                    input_file_text.append('**Node sets for every single node created by Python \n')
                    for node_set in node_sets_dict.values():
                        input_file_text.append(f'{node_set} \n')

                elif '** bc_python_fill_in_placeholder' in line:
                    input_file_text.append('**Boundary conditions created by Python \n')
                    input_file_text.append('*Boundary \n')
                    for bc in bc_dict.values():
                        input_file_text.append(f'{bc} \n')

                else:
                    input_file_text.append(f'{line} \n')

            input_file.write_text(''.join(map(str, input_file_text)))
            self.log.info(f'Abaqus input file created successfully and saved at {input_file}')

            return input_file

        except Exception as err:
            self.log.error(str(err))
            return 0

    def write_input_file_restart(self, set_work_name: str, job_name: str, previous_input_file: str, step_name: str,
                                 restart_step: str, resume: bool = True):
        """
        This function modifies the previous input file and saves it in instances output folder with the name
         'job_name'.inp. This new file is a Abaqus restart input file.

        Args:
            set_work_name: Name to load/save the set in instance
            job_name: Name of the Abaqus job
            previous_input_file: Path of the privious Abaqus input file
            step_name: name of the step
            restart_step: step from where to restart
            resume: Tells if the simulation shall start from the beginning or if the last step shall be resumed.

        Returns:
            written input file (path)
        """

        if set_work_name in self.node_set:
            if 'sets' in self.node_set[set_work_name] and 'boundary_conditions' in self.node_set[set_work_name]:
                bc_dict = self.node_set[set_work_name]['boundary_conditions']
            else:
                self.log.error(f'Boundary conditions and/or node sets are not created in '
                               f'set_work_name {set_work_name}. Use .create_boundary_condition() first.')
                return 0
        else:
            self.log.error(f'Set_work_name {set_work_name} not found in {self.node_set.keys()}')
            return 0

        try:
            previous_input_file = Path(previous_input_file)
            if not previous_input_file.is_file():
                self.log.error(f'Previous input file cannot be found at {previous_input_file}')
                return 0

            # Read input file and save in an array
            previous_input_file_data = previous_input_file.read_text().split('\n')

            input_file = self.paths['output'] / f'{job_name}.inp'

            input_file_text = []

            copy_input_file = 0

            # Write restart headline
            self.log.debug('Write Header')
            input_file_text.append(f'** Description: \n')
            input_file_text.append(f'** Restart for input file: {previous_input_file} \n')
            input_file_text.append(f'** ---------------------------------------------------------------- \n')
            input_file_text.append(f'*Heading \n')
            input_file_text.append(f'*Restart, read, step={str(restart_step)} \n')

            # If the simulation shall not be resumed, all steps (but Geostatic-Step) will be copied
            # into the new input file
            if not resume:
                for line in previous_input_file_data:
                    if '** restart_point_python_placeholder' in line:
                        copy_input_file = 1

                    if copy_input_file:
                        input_file_text.append(line)

            # Write new step
            self.log.debug('Begin Step')  # TODO Possibility to modify step parameters
            input_file_text.append(f'** \n')
            input_file_text.append(f'** STEP:{step_name} \n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'*Step, name={step_name}, nlgeom=NO, amplitude=RAMP, inc=10000 \n')
            input_file_text.append(f'*Soils, consolidation, end=PERIOD, utol=50000., creep=none \n')
            input_file_text.append(f'6000., 43200., 1e-05, 6000., \n')

            self.log.debug(f'Step: Adding boundary conditions')
            input_file_text.append(f'** \n')
            input_file_text.append(f'** BOUNDARY CONDITIONS \n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'** Name: BC_PP Type: Pore pressure \n')

            input_file_text.append(f'**Boundary conditions created by Python \n')
            input_file_text.append(f'*Boundary \n')
            for bc in bc_dict.values():
                input_file_text.append(f'{bc} \n')

            self.log.debug('Step: Adding output request')
            input_file_text.append(f'** \n')
            input_file_text.append('** OUTPUT REQUESTS' + '\n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'** *Restart, write, frequency = 1 \n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'** FIELD OUTPUT: F - Output - 1 \n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'*Output, field \n')
            input_file_text.append(f'*Node Output \n')
            input_file_text.append(f'CF, COORD, POR, RF, U \n')
            input_file_text.append(f'*Element Output, directions = YES \n')
            input_file_text.append(f'FLUVR, LE, S, SAT, VOIDR, NFORC \n')
            input_file_text.append(f'*Contact Output \n')
            input_file_text.append(f'CDISP, CSTRESS, PFL \n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'** HISTORY OUTPUT: H - Output - 1 \n')
            input_file_text.append(f'** \n')
            input_file_text.append(f'*Output, history, variable = PRESELECT \n')
            input_file_text.append(f'*EL FILE, frequency=10000 \n')
            input_file_text.append(f'COORD, VOIDR, POR \n')
            input_file_text.append(f'*NODE FILE \n')
            input_file_text.append(f'COORD \n')
            input_file_text.append(f'*End Step \n')
            self.log.debug(f'End Step')

            input_file.write_text(''.join(map(str, input_file_text)))
            self.log.info(f'Abaqus restart input file created successfully and saved at {input_file}')

            return input_file

        except Exception as err:
            self.log.error(str(err))
            return 0

    def set_path(self, path_name, path):
        """
        Set paths, for example scratch or output path.

        Args:
            path_name: name of the path in instance
            path: actual path

        Returns:
            boolean: true on success
        """
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

    def write_bash_file(self, path: Path, input_file_path: str, user_subroutine_path: str = None, use_scratch_path: bool = False,
                        additional_parameters: str = None, old_job_name: str = None):
        """ Function to create bash file, depending on the subsystem (windows or linux) to execute Abaqus
            simulation in console.

         Parameters:
            path (Path): Where to save the bash file
            input_file_path (str): Input filename including path
            user_subroutine_path (str): User subroutine filename including path (optional)
            use_scratch_path (bool): Shall a scratch folder be used. Folder has to be defined via function
            .set_path('scratch') (optional)
            old_job_name (str): name of the old job (optional)
            additional_parameters (str): Additional parameters to be used for the execution of the simulation (optional)

        Returns:
            bash_file_name (String)
        """

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
                bash_file = path / f'{job_name}.bat'

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

    def read_csv_file(self, file: str, delimiter: str = ','):
        """ Function to read an csv-file-export from the Software Simulia Abaqus

         Parameters:
            file (str): filename including path
            delimiter (str), optional: delimiter used in ascii file

        Returns:
            ndarray(dict)
        """

        try:
            file = Path(file)

            if not file.is_file():
                self.log.error(f'File {file} not found.')
                raise FileNotFoundError

            self.log.info(f'Load Abaqus-Mesh-File: {file}')

            with file.open('r') as csv_file:
                read_csv = csv.reader(csv_file, delimiter=delimiter)

                lines = []

                for row in read_csv:
                    try:
                        if len(row) == 4:
                            lines.append({'x_coordinate': float(row[0]),
                                          'y_coordinate': float(row[1]),
                                          'z_coordinate': float(row[2]),
                                          'value': float(row[3])})

                        if len(row) != 4:
                            self.log.info(f'Empty row found or transition failed. Continue...')

                    except Exception as err:
                        self.log.info(f'Empty row found or transition failed. Continue... [{err}]')

                self.log.debug(f'{len(lines)} rows read successfully', )

                return lines

        except Exception as err:
            self.log.error(f'File --{file}-- could not be read correctly [{err}]')
            return 0

    def write_csv_file(self, data_array, file, delimiter: str = ','):
        """ Function to write an csv-file-input from a given ndarray for the Software Simulia Abaqus

         Parameters:
            data_array (ndarray): data set
            file (str): filename including path
            delimiter (str), optional: delimiter used in ascii file

        Returns:
            boolean: true on success
        """

        try:

            file = Path(file)

            if not Path(file.parent[0]).is_dir():
                self.log.error(f'Path to save file into {file.parent[0]} not found.')
                raise FileNotFoundError

            self.log.info(f'Write Abaqus-data-file: {file}')

            # Writing data to csv-file
            numpy.savetxt(file, data_array, delimiter=delimiter, fmt='%11.8s')

            return True

        except Exception as err:
            self.log.error(f'Writing data in  --{file}-- not successful. [{err}]')
            return False

    def preprocessing(self):  # TODO
        return 0

    def postprocessing(self):  # TODO
        return 0