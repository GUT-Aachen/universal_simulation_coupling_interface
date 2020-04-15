import logging as log
import numpy
from pathlib import Path


class AbaqusInputFile:
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
            log.error(f'Expected an Simulia Abaqus Inputfile with .inp suffix instead of {self.input_file.suffix}')
            raise FileNotFoundError

        # Read input file and save in an array
        self.data = self.input_file.read_text().split('\n')

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

    def get_nodes(self, part_name):
        """ Function to create an array consisting of all node number and the corresponding coordinates. Full path of
            the input file must be passed. The name of the part one want to extract the node-coordinates must be passed
            as well. The part name is not case sensitive! If parts are independent and meshed at the assembly, then the
            name of the assembly must be set as part_name input parameter.

         Parameters:
            part_name (String): Name of the part/assembly

        Returns:
            dict: Containing nodes and corresponding coordinates for each node in part_name {x_coordinate, y_coordinate,
             z_coordinate, node_number}
        """

        try:

            # Coordinates of nodes can be stored in part or in assembly therefore two search strings
            # (case insensitive) have to be created.
            part_string = '*Part, name=' + part_name
            part_string = part_string.lower()
            assembly_string = '*Instance, name=' + part_name
            assembly_string = assembly_string.lower()

            # Variable set to True when node information have been found.
            read_coordinates = False

            # Initialize empty arrays for nodes and coordinates. These will be assembled after filling with data.
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

            # Return ndarray containing a set of nodes and the corresponding coordinates.
            self.log.info('Added %s nodes with x/y/z-coordinates', len(node_list))

            if not len(node_list) == 0:
                return node_list
                # return {'x' : x_array, 'y' : y_array, 'z' : z_array, 'node' : node_array}

            else:
                self.log.error('No nodes found for part: %s. Abort!', part_name)
                exit()

        except Exception as err:
            self.log.error(str(err))
            return -1

        finally:
            log.debug('Exit function')
