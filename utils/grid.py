import logging as log
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

    def add_node(self, node_number, x_coordinate, y_coordinate, z_coordinate=None, values=None):
        """
        Adding a node to the grid.

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
                existing_node = self.coordinates_exist(x_coordinate, y_coordinate, z_coordinate)
                if existing_node:
                    self.log.error(f'Coordinates already assigned. {self[existing_node]}')
                else:
                    self.nodes[node_number] = Node(node_number, x_coordinate, y_coordinate, z_coordinate, values)
                    return self.nodes[node_number]
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
            existing_node = self.coordinates_exist(x_coordinate, y_coordinate, z_coordinate)
            if existing_node and not existing_node == node_number:
                self.log.error(f'Coordinates already assigned. {self[existing_node]}')
            else:
                self.nodes[node_number] = Node(node_number, x_coordinate, y_coordinate, z_coordinate, values)
                return 0
        else:
            self.log.error(f'Node number {node_number} does not exist.')

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
