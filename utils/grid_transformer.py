import logging as log
from utils.grid import Grid
from scipy.spatial import KDTree
import numpy
import matplotlib.pyplot as plt  # used for visualisation of transformation validation


class GridTransformer:

    def __init__(self):
        self.log = log.getLogger(self.__class__.__name__)

        self.grids = {}
        self.transformation = []

    def __str__(self):
        return f'{self.__class__.__name__} contains: grids={len(self.grids)}'

    def add_grid(self, grid: Grid, grid_name: str):
        """
        Add a grid to the instance.

        Args:
            grid: Grid to be added.
            grid_name: Name of the grid in the instance.

        Returns:
            boolean: true on success
        """
        if grid_name in self.grids:
            self.log.error(f'Grid with name {grid_name} already exists. Please use .update_grid() instead.')
            return False
        else:
            self.grids[grid_name] = {}
            self.grids[grid_name]['transform'] = {}
            self.grids[grid_name]['grid'] = grid
            self.log.debug(f'Grid {grid_name} added')
            return True

    def update_grid(self, grid: Grid, grid_name: str):
        """
            Update a grid in instance. The available grid will be deleted and replaced by the new grid.
        Args:
            grid: Grid to be added.
            grid_name: Name of the grid in the instance.

        Returns:
            boolean: true on success
        """
        if grid_name not in self.grids:
            self.log.error(f'Grid with name {grid_name} does not exists. Please use .add_grid() instead.')
            return False
        else:
            del self.grids['grid_name']
            self.grids[grid_name] = {}
            self.grids[grid_name]['transform'] = {}
            self.grids[grid_name]['grid'] = grid
            self.log.debug(f'Grid {grid_name} added')
            return True

    def find_nearest_neighbors(self, grid_name_1: str, grid_name_2: str, neighbors_quantity: int = 10,
                               distance_max: float = None):
        """
        To tranfer the data from one grid to another a modified nearest neighbor approach is used. This method takes
        the coordinates of each point in two grids and searches for nearest neighbors. Thereby the first grid is the
        source and the second grid is the target, means that for each node in the target neighbors in the source are
        found. The amount of neighbors used for each node is set with the optional parameter neighbors_quantity.
        Even if the density of neighbor nodes all over the grid seems to be good, there are some minor problems at
        the edges, especially at the corners. In the corners the distance to the neighbors vary very much. The
        parameter distance_max helps with this issue, as one can set a maximum distance between the node and a
        neighbor. The results are stored in the instance and are used by the function .transition() to transfer
        the data from one grid to another. This saves time, as the fitting of the grids is done only once.

        Args:
            grid_name_1 (str): Name of the first grid (source)
            grid_name_2 (str): Name of the second grid (target)
            neighbors_quantity (int, optional): Number of neighbors to use
            distance_max (int, optional): maximum distance between node and neighbors

        Returns:
            boolean: true on success
        """

        # Check if grids exist
        if grid_name_1 not in self.grids:
            self.log.error(f'Grid with name "{grid_name_1}" not found in {self.grids.keys()}')
            return False

        if grid_name_2 not in self.grids:
            self.log.error(f'Grid with name "{grid_name_2}" not found in {self.grids.keys()}')
            return False

        # Transform grids to arrays containing the coordinates to use KDTree
        grid_1_coordinates = self.grids[grid_name_1]['grid'].get_coordinates_array()
        grid_1_nodes = list(self.grids[grid_name_1]['grid'].nodes.keys())
        grid_2_coordinates = self.grids[grid_name_2]['grid'].get_coordinates_array()
        grid_2_nodes = list(self.grids[grid_name_2]['grid'].nodes.keys())

        # Check for nearest neighbor
        tree = KDTree(grid_1_coordinates)
        dist, points = tree.query(grid_2_coordinates, neighbors_quantity)

        transform_dict = {}

        # Iterate through the results to put them into a dictionary. Additionally the maximum distance will be
        # checked.
        for i in range(len(dist)):
            # Initialize the dictionary entry for a node
            transform_dict[grid_2_nodes[i]] = []

            # Loop through all neighbors and check distance
            for k in range(len(dist[i])):  # FIXME problems when only 1 neighbor is used, because no list in dist
                node = grid_1_nodes[points[i][k]]
                distance = dist[i][k]

                # Easily just continue when the maximum distance is exceeded
                if distance_max:
                    if distance > distance_max:
                        continue

                # Append node and distance to list in dictionary
                transform_dict[grid_2_nodes[i]].append({'node_number': node, 'distance': distance})

            # Check if at least one neighbor was found according to the maximum distance. Otherwise exit method and
            # and log an error.
            if len(transform_dict[grid_2_nodes[i]]) == 0:
                self.log.error(f'No neighbor found for node {grid_2_nodes[i]} in {grid_name_2}')
                return False

        self.grids[grid_name_2]['transform'][grid_name_1] = transform_dict
        self.log.info(f'Nearest neighbors in {grid_name_1} found for {grid_name_2}')

        return True

    def transition(self, src_grid_name, value_name, target_grid_name):
        """
        The values (value_name) of the source grid (src_grid_name) are transfered to the target grid
        (target_grid_name). For the transfer a modified nearest neighbor approach is used (see
        .find_nearest_neighbors()). The relevant neighbors and their distance to the corresponding node are stored.
        This function used the distance from the node to calculate a weighted average.

        Args:
            src_grid_name (str): Name of the source grid
            value_name: Name of the values in source grid
            target_grid_name (str): Name of the target grid

        Returns:
            boolean: true on success
        """
        # Check if grids exist
        if src_grid_name not in self.grids:
            self.log.error(f'Grid with name "{src_grid_name}" not found in {self.grids.keys()}')
            return False
        if target_grid_name not in self.grids:
            self.log.error(f'Grid with name "{target_grid_name}" not found in {self.grids.keys()}')
            return False

        # Check if value exists in src_grid
        src_grid = self.grids[src_grid_name]
        target_grid = self.grids[target_grid_name]
        if not src_grid['grid'].get_node_values(value_name):
            self.log.error(f'Value_name ({value_name}) not found in nodes.')
            return False

        src_values = src_grid['grid'].get_node_values(value_name)

        # Check if neighbors for this combination have been set
        if src_grid_name not in target_grid['transform']:
            self.log.error('No transformation matrix has been found. Before transformation neighbors have to be found.')
            return False

        for node, node_dict in target_grid['transform'][src_grid_name].items():
            sum_distance = 0
            factor = 0

            # Calculating of the weighted average
            for item in node_dict:
                distance = item['distance']
                node_number = item['node_number']

                sum_distance += distance
                value = src_values[node_number]

                factor += value * distance

            result = factor / sum_distance
            target_grid['grid'].nodes[node].set_value(value_name, result)

        self.log.info(f'Transition for {value_name} from {src_grid_name} to {target_grid_name} successful')
        return True

    def nearest_neighbors_stat(self, grid_name):
        """
        The mentioned grid and the established connections to other grids are (statistically) examined
        in this function and the results are output in the log.

        Args:
            grid_name: Name of the grid, to be examined

        Returns:
            boolean: true on success
        """
        # Check if grids exist
        if grid_name not in self.grids:
            self.log.error(f'Grid with name "{grid_name}" not found in {self.grids.keys()}')
            return False

        self.log.info(f'Statistics for: {grid_name}')
        self.log.info(f'Nodes: {len(self.grids[grid_name]["grid"])}')

        for grid, node_list in self.grids[grid_name]['transform'].items():
            distances = []

            for node, node_dict in node_list.items():
                for item in node_dict:
                    distances.append(item['distance'])

            distances = numpy.array(distances)

            self.log.info(f'Neighborhood to: {grid}')
            self.log.info(f'\t Number of neighbors in total: {len(distances)}')
            self.log.info(f'\t Mean: {numpy.nanmean(distances)}')
            self.log.info(f'\t Std. Deviation: {numpy.nanstd(distances)}')
            self.log.info(f'\t Min: {numpy.ndarray.min(distances)}')
            self.log.info(f'\t Max: {numpy.ndarray.max(distances)}')

        self.log.info(f'End of Statistics')

        return True

    def transformation_validation(self, src_grid_name, value_name, target_grid_name):
        """ Validating the method of transferring data from one grid to another. There are two different grids (one is
        maybe coarser then the other). The information within the grid is transferred from one grid to the other and
        backwards. The transformation form a (e.g. finer) to b (e.g. coarser) includes data loss. The amount of loss
        is influenced by the difference of the grid resolution. The following code transforms the data from the
        source grid (src_grid_name) to the target grid (target_grid_name) and back to the source grid.
        The data loss will be shown by checking the difference 'source - source_re'. As a result one
        get a min/max-value, mean and standard deviation to check whether the data loss is acceptable. In addition
        a plot is created to be able to make a visual check.

        Parameters:
            src_grid_name (str): name of source grid
            target_grid_name (str): name of target grid
            value_name (str): name of values in source grid

        Returns:
            None
        """

        try:
            # Data transformation from input_mesh to output_mesh
            # output = mesh_transformation(input_mesh, output_mesh, input_data)
            src_grid_begin = self.grids[src_grid_name]['grid']
            data_begin = numpy.array(list(src_grid_begin.get_node_values(value_name).values()))
            target_grid = self.grids[target_grid_name]['grid']

            self.transition(src_grid_name, value_name, target_grid_name)
            self.transition(target_grid_name, value_name, src_grid_name)

            src_grid_end = self.grids[src_grid_name]['grid']
            data_end = numpy.array(list(src_grid_end.get_node_values(value_name).values()))

            self.log.info('Array output: input after retransformation')

            # Calculating mean and standard deviation
            # For statistics the absolute values of fine_new_data are used
            diff = numpy.absolute(data_begin - data_end)

            self.log.info(f'Statistics:')
            self.log.info(f'Source Grid: {src_grid_begin}')
            self.log.info(f'Target Grid: {target_grid}')
            self.log.info(f'After transformation:')
            self.log.info(f'NaN-Values: {sum(numpy.isnan(data_end))}')
            self.log.info(f'Mean: {numpy.nanmean(diff)}')
            self.log.info(f'Std. Deviation: {numpy.nanstd(diff)}')
            self.log.info(f'Mean Match: {numpy.nanmean(numpy.absolute(data_end / data_begin))}')
            self.log.info(f'Std. Deviation: {numpy.nanstd(numpy.absolute(data_end / data_begin))}')
            self.log.info(f'Worst Match: {numpy.ndarray.max(numpy.absolute(data_end / data_begin))}')
            self.log.info(f'Worst Match: {numpy.ndarray.min(numpy.absolute(data_end / data_begin))}')

            # Generating the visual output
            self.log.info('Plotting datasets to visually comparison')
            mpl_fig = plt.figure()
            ax1 = mpl_fig.add_subplot(221)
            cb1 = ax1.scatter(list(src_grid_begin.get_node_values('x_coordinate').values()),
                              list(src_grid_begin.get_node_values('y_coordinate').values()),
                              s=1, c=data_begin, cmap=plt.cm.get_cmap('RdBu'))
            plt.colorbar(cb1, ax=ax1)
            ax1.set_title('input (original)')
            ax2 = mpl_fig.add_subplot(222)
            cb2 = ax2.scatter(list(target_grid.get_node_values('x_coordinate').values()),
                              list(target_grid.get_node_values('y_coordinate').values()),
                              s=1, c=list(target_grid.get_node_values('data').values()), cmap=plt.cm.get_cmap('RdBu'))
            plt.colorbar(cb2, ax=ax2)
            ax2.set_title('output')

            ax3 = mpl_fig.add_subplot(223)
            cb3 = ax3.scatter(list(src_grid_end.get_node_values('x_coordinate').values()),
                              list(src_grid_end.get_node_values('y_coordinate').values()),
                              s=1, c=data_end, cmap=plt.cm.get_cmap('RdBu'))
            plt.colorbar(cb3, ax=ax3)
            ax3.set_title('input (retransformation)')

            # function to show the plot
            plt.show()

            return True

        except Exception as err:
            self.log.critical('Execution aborted! [%s]', str(err))
            return False
