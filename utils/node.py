import logging as log
import math


class Node:
    """
    This class represents one node within a grid.

    Args:
            node_number (int): number of the node
            x_coordinate (float): x-coordinate
            y_coordinate (float): y-coordinate
            z_coordinate (float, optional): z-coordinate
            values (dict, optional): dictionary of values
    """

    def __init__(self, node_number, x_coordinate, y_coordinate, z_coordinate=None, values=None):
        self.log = log.getLogger(self.__class__.__name__)

        # Check input parameters
        if not isinstance(node_number, int):
            raise TypeError(f'Input parameter node_number must be of type integer is {type(node_number)}.')
        if not isinstance(x_coordinate, int) and not isinstance(x_coordinate, float):
            raise TypeError(f'Input parameter x_coordinate must be of type float or integer is {type(x_coordinate)}.')
        if not isinstance(y_coordinate, int) and not isinstance(y_coordinate, float):
            raise TypeError(f'Input parameter y_coordinate must be of type float or integer is {type(y_coordinate)}.')
        if not isinstance(z_coordinate, int) and not isinstance(z_coordinate, float) and z_coordinate is not None:
            raise TypeError(f'Input parameter z_coordinate must be of type float, integer or left empty is {type(z_coordinate)}.')

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
        A tuple of coordinates (x,y,z) will be returned. If no z-coordinate is assigned to the node, 0 will be returned
        for z-coordinate.

        Returns: A tuple of coordinates (x,y,z).

        """
        if self.z_coordinate:
            return self.x_coordinate, self.y_coordinate, self.z_coordinate
        else:
            return self.x_coordinate, self.y_coordinate, 0

    def z_rotation(self, angle=None, origin: dict = None):
        """Rotate this node by a given angle at a origin point
        Args:
            angle (float/int, optional): sets the rotation angle in degrees (0 to 360°)
            origin (float/int, optional): origin/fix point for rotation

        Returns:
            True on success
        """

        # Check input parameters
        if not isinstance(angle, int) and not isinstance(angle, float) and angle is not None:
            raise TypeError(f'Input parameter angle must be of type float or integer is {type(angle)}.')
        elif angle < 0 or angle > 360:
            raise ValueError(f'Input parameter angle must fulfull 0 < angle < 360.')

        if not isinstance(origin, dict) and origin is not None:
            raise TypeError(f'Input parameter origin must be of type dict is {type(origin)}.')
        else:
            # Check if keys for x and y coordinates are given
            x_coordinate_exists = False
            y_coordinate_exists = False
            for key in origin.keys():
                if key == "x_coordinate":
                    x_coordinate_exists = True
                elif key == "y_coordinate":
                    y_coordinate_exists = True

            if not x_coordinate_exists or not y_coordinate_exists:
                raise KeyError(f'Input parameter origin must consist of a dictionary containing a key "x_coordinate" '
                               f'and y_coordinate containing the particular coordinates.')

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
