import logging as log
import math


class Node:
    """
    This class represents one node within a grid.

    Args:
            node_number: number of the node
            x_coordinate: x-coordinate
            y_coordinate: y-coordinate
            z_coordinate: z-coordinate (optional)
            values: dictionary of values (optional)
    """
    def __init__(self, node_number, x_coordinate, y_coordinate, z_coordinate=None, values=None):
        self.log = log.getLogger(self.__class__.__name__)
        self.node_number = node_number
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.z_coordinate = z_coordinate
        if isinstance(values, dict):
            self.values = values
        elif values:
            self.log.error(f'Dict for "values" expected, but got {values}')
        else:
            self.values = {}

    def __str__(self):
        return f'{self.__class__.__name__}: no={self.node_number}, coordinates={self.coordinates}, values={self.values}'

    @property
    def coordinates(self):
        """
        A tuple of coordinates (x,y,z) will be returned. If no z-coordinate is assigned to the node 0 will be returned
        for z-coordinate.

        Returns: A tuple of coordinates (x,y,z).

        """
        if self.z_coordinate:
            return self.x_coordinate, self.y_coordinate, self.z_coordinate
        else:
            return self.x_coordinate, self.y_coordinate, 0

    def z_rotation(self, angle=None, origin=None):
        """Rotate the node by a given angle at a origin point
        Args:
            angle: optional
                sets the rotation angle
            origin: optional
                origin/fix point for rotation

        Returns:
            True on success
        """

        if not angle or not origin:
            raise ValueError(f'An rotation angle and an origin must be defined.')

        x = self.x_coordinate - origin['x_coordinate']
        y = self.y_coordinate - origin['y_coordinate']

        x_rotated = x * math.cos(angle) + y * math.sin(angle)
        y_rotated = x * -math.sin(angle) + y * math.cos(angle)

        self.x_coordinate = x_rotated + origin['x_coordinate']
        self.y_coordinate = y_rotated + origin['y_coordinate']

        return True

    def get_value(self, value_name):
        """
        Get a particular value assigned to the node. In addition to the stored values it is also possible to
        use 'x', 'y', or 'z' to get the corresponding coordinate.

        Args:
            value_name: name of the value

        Returns: value, 0 if value_name not exists

        """

        try:
            if value_name == 'x' or value_name == 'x_coordinate':
                return self.x_coordinate
            elif value_name == 'y' or value_name == 'y_coordinate':
                return self.y_coordinate
            elif value_name == 'z' or value_name == 'z_coordinate':
                return self.z_coordinate
            else:
                return self.values[value_name]
        except KeyError as err:
            self.log.error(f'get_value() {err}')
            return False

    def set_value(self, value_name, value):
        """
        Add a new or update an existing value.

        Args:
            value_name: name of the value
            value: value

        Returns: 0 if successful

        """
        if value_name in self.values:
            self.values[value_name] = value
            # self.log.debug(f'{value_name} updated to {value}')
            return 0
        else:
            self.values[value_name] = value
            # self.log.debug(f'{value_name} added and set to {value}')
            return 0
