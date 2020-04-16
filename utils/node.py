import logging as log


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
        self.coordinate_x = x_coordinate
        self.coordinate_y = y_coordinate
        self.coordinate_z = z_coordinate
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
        if self.coordinate_z:
            return self.coordinate_x, self.coordinate_y, self.coordinate_z
        else:
            return self.coordinate_x, self.coordinate_y, 0

    def get_value(self, value_name):
        """
        Get a particular value assigned to the node. In addition to the stored values it is also possible to
        use 'x', 'y', or 'z' to get the corresponding coordinate.

        Args:
            value_name: name of the value

        Returns: value, 0 if value_name not exists

        """

        try:
            if value_name == 'x':
                return self.coordinate_x
            elif value_name == 'y':
                return self.coordinate_y
            elif value_name == 'z':
                return self.coordinate_z
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
            self.log.debug('%s updated to %f', value_name, value)
            self.values[self.values] = value
            return 0
        else:
            self.log.debug('%s added and set to %f', value_name, value)
            self.values[self.values] = value
            return 0
