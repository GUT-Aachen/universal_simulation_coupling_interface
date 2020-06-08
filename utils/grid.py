import logging as log
import numpy
from utils.node import Node


class Grid:
    """This class represents a grid of nodes"""
    def __init__(self):
        self.log = log.getLogger(self.__class__.__name__)
        self.nodes = {}

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, node_number):
        if isinstance(node_number, int):
            if node_number in self.nodes:
                return True
            else:
                return False
        else:
            self.log.error(f'Integer expected got {node_number}')
            return False

    def __getitem__(self, node_number):
        try:
            return self.nodes[node_number]
        except KeyError as err:
            self.log.error(f'get_node() {err}')
            return 0

    def __str__(self):
        return f'{self.__class__.__name__}: number of nodes={len(self)}'

    def get_available_values(self):
        """
        Returns a list of available names for values in grid instance.

        Returns:
            list: available value_names in grid
        """
        str_output = []

        for node in self.nodes.values():
            for value_name in node.values.keys():
                str_output.append(value_name)
            break

        return str_output

    def check_value_set_completeness(self, set_name):
        """ Check if a value is stored for each node in the grid. Otherwise NaN will be stored in those nodes."""

        self.log.debug(f'Check if values for {set_name} are set for any node in this grid.')

        counter = 0

        for node in self.nodes.values():
            try:
                if not node.values[set_name]:
                    node.values[set_name] = numpy.nan
                    counter += 1
            except Exception:
                node.values[set_name] = numpy.nan
        if not counter == 0:
            self.log.debug(f'Check completed. Added NaN value for {counter} nodes.')
        else:
            self.log.debug(f'Check completed. Data valid.')

        return True

    def get_empty_nodes(self):
        """ Getting a dictionary containing all nodes without values. This dict can be used to be filled with values
        and set back to the grid using the method .set_node_values().

        Returns:
            dictionary including all nodes as keys with None as value
        """
        try:
            node_number_dict = {}

            for node_number in self.nodes.keys():
                node_number_dict[node_number] = None

            if len(node_number_dict):
                return node_number_dict
            else:
                return False

        except Exception as err:
            log.error(f'An error occured while reading values: {err}')
            return 0

        except KeyError as err:
            log.error(f'Key {node_number} not found. {err}')
            return 0

    def get_coordinates_array(self):
        """
        Returns a tuple of coordinates

        Returns:
            tuple of coordinates
        """
        coordinates = []

        for node in self.nodes.values():
            coordinates.append(node.coordinates)

        return coordinates

    def get_list(self):
        """
        Returns a tuple of all saved grid data

        Returns:
            tuple
        """

        data = []

        for node in self.nodes.values():
            line = []
            for row in node.coordinates:
                line.append(row)

            for item in node.values.values():
                line.append(item)

            data.append(line)

        return data

    def set_node_values(self, value_name: str, node_dict: dict, ):
        """
        Saving value-node-combinations from a dictionary to the nodes in the grid.

        Args:
            node_dict (dict): dictionary consisting of node_number:value combinations
            value_name (str): name for the value

        Returns:
            boolean: true on success
        """
        # Check if nodes included in dict fits with grid
        for node_number in node_dict.keys():
            if node_number not in self.nodes.keys():
                self.log.error(f'At least one node from input (node {node_number}) is not available in this grid.')
                raise ValueError

        for node_number, value in node_dict.items():
            self.nodes[node_number].set_value(value_name, value)

        self.check_value_set_completeness(value_name)

        return True

    def get_node_values(self, value_name: str):
        """
        Function to get a dictionary including all nodes and the corresponding value. Any value, stored in the
            node instance can be called.

        Args:
            value_name: value of interest

        Returns:
            dict of node: value pairs
        """
        try:
            node_value_dict = {}

            for node in self.nodes.values():
                value = node.get_value(value_name)
                if isinstance(value, int) or isinstance(value, float):
                    node_value_dict[node.node_number] = value

            if len(node_value_dict):
                return node_value_dict
            else:
                return False

        except Exception as err:
            log.error(f'An error occured while reading values: {err}')
            return 0

        except KeyError as err:
            log.error(f'Key {value_name} not found. {err}')
            return 0

    def add_node(self, node_number, x_coordinate, y_coordinate, z_coordinate=None, values=None):
        """
        Adding a node to the grid. Each node number must be used just once, otherwise an error is thrown.

        Args:
            node_number: node number of the new node (optional)
            x_coordinate: x-coordinate
            y_coordinate: y-coordinate
            z_coordinate: z-coordinate
            values: dictionary of values

        Returns: added node

        """
        if node_number in self:
            self.log.error(f'Node with node_number {node_number} already exists with coordinates'
                           f' {self.nodes[node_number].coordinates}')
        else:
            if isinstance(node_number, int):
                self.nodes[node_number] = Node(node_number, x_coordinate, y_coordinate, z_coordinate, values)
                return 0
            else:
                self.log.error(f'Integer expected got {node_number}')

    def set_node(self, node_number, x_coordinate, y_coordinate, z_coordinate=None, values=None):
        """
        Modify an existing node. For adding a new node function add_node() has to be used.

        Args:
            node_number: Number of the node to be modified.
            x_coordinate: x-coordinate
            y_coordinate: y-coordinate
            z_coordinate: z-coordinate
            values: dictionary of values

        Returns: 0 if successful

        """
        if node_number in self:
            self.nodes[node_number] = Node(node_number, x_coordinate, y_coordinate, z_coordinate, values)
            return 0
        else:
            self.log.error(f'Node number {node_number} does not exist.')

    def rename_value_set(self, old_name, new_name):
        """
        Rename a value in each nodes at a time.

        Args:
            old_name: Old name of the value
            new_name: New name of the value

        Returns:

        """
        try:
            for node in self.nodes.values():
                if old_name in node.values:
                    node.values[new_name] = node.values[old_name]
                    del(node.values[old_name])

            return True
        except Exception as err:
            self.log.error(f'An error occurred while renaming values: {err}')
            return False

    def z_rotation(self, angle=None, origin=None):
        """Rotate grid by a given angle at a origin point.
        Args:
            angle: optional
                sets the rotation angle
            origin: optional
                origin/fix point for rotation

        Returns:
            True on success
        """
        for node in self.nodes.values():
            node.z_rotation(angle, origin)

    def initiate_grid(self, data_set, value_name=None, clear_first=True):
        """
        Initiate a new grid by transferring a dictionary including x/y/z-direction, values and optional node_number.
        Existing grid nodes will be removed first.

        Args:
            data_set: dict including grid information
            value_name: name of the values
            clear_first: shall the grid be cleared before importing data set?

        Returns:
            boolean: true on success
        """

        try:
            if isinstance(data_set, list):

                if clear_first and len(self.nodes) > 0:
                    self.log.warning(f'Grid is not empty ({len(self.nodes)}). Grid will be vanished for initialization.')
                    self.nodes = {}

                i = -1

                for row in data_set:
                    i += 1
                    input_dict = {}

                    if 'x_coordinate' in row:
                        input_dict['x_coordinate'] = row['x_coordinate']
                    else:
                        self.log.error(f'No x_coordinate found in {row}')
                        return False

                    if 'y_coordinate' in row:
                        input_dict['y_coordinate'] = row['y_coordinate']
                    else:
                        self.log.error(f'No y_coordinate found in {row}')
                        return False

                    if 'z_coordinate' in row:
                        input_dict['z_coordinate'] = row['z_coordinate']

                    if 'value' in row:
                        if value_name:
                            input_dict['values'] = {value_name: row['value']}
                        else:
                            input_dict['values'] = {'data': row['value']}

                    if 'values' in row:
                        if isinstance(row['values'], dict):
                            input_dict['values'] = row['values']

                        else:
                            self.log.warning(f'Input dictionary pretends to include a dictionary for values, but '
                                             f'found {type(row["values"])}.')

                    if 'node_number' in row:
                        input_dict['node_number'] = row['node_number']
                    else:
                        input_dict['node_number'] = i

                    self.add_node(**input_dict)

            self.log.info(f'Added {len(data_set)} nodes to the grid.')

            return True

        except Exception as err:
            self.log.error(f'An error occurred while adding nodes to the grid. [{err}]')
            raise Exception

    def coordinates_exist(self, x_coordinate, y_coordinate, z_coordinate=None):
        """
        Checks whether the given coordinates are already assigned to a node. If so, the particular node_number will
        be returned, otherwise return is 0.

        Args:
            x_coordinate: x coordinate
            y_coordinate: y coordinate
            z_coordinate: z coordinate (optional)

        Returns: assigned node_number or 0

        """
        for node_number, node in self.nodes.items():
            if z_coordinate:
                if node.coordinates == (x_coordinate, y_coordinate, z_coordinate):
                    return node_number
            else:
                if node.coordinates == (x_coordinate, y_coordinate, 0):
                    return node_number
        return 0

    def find_node(self, x_coordinate, y_coordinate, z_coordinate=None):
        """
        Checks whether the given coordinates are already assigned to a node. If so, the particular node_number will
        be returned, otherwise return is 0.

        Args:
            x_coordinate: x coordinate
            y_coordinate: y coordinate
            z_coordinate: z coordinate (optional)

        Returns: assigned node_number or 0

        """
        for node_number, node in self.nodes.items():
            if z_coordinate:
                if node.coordinates == (x_coordinate, y_coordinate, z_coordinate):
                    return node_number
            else:
                if node.coordinates == (x_coordinate, y_coordinate, 0):
                    return node_number
        return 0

    def grid_validation_check(self):
        """
        Checking the grid for any issues like:
            1. Using the same coordinates in two different nodes

        Returns: 0 if no errors occurred

        """

        error = 0

        for node_number_a, node_a in self.nodes.items():
            for node_number_b, node_b in self.nodes.items():
                if node_number_a == node_number_b:
                    continue
                if node_a.coordinates == node_b.coordinates:
                    log.error(f'Node {node_number_a} and node {node_number_b} are sharing the same'
                              f' coordinates ({node_a.coordinates})')
                    error += 1

        if not error:
            return 0
        else:
            return error
