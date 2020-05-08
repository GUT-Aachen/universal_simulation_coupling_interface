import random
import statistics
import numpy
import logging as log
import matplotlib.pyplot as plt  # used for visualisation of transformation validation


class GaussRandomizeGrid:
    """ GaussRandomizeGrid is used to randomize the content of a dictionary or a list. """

    def __init__(self):

        self.log = log.getLogger(self.__class__.__name__)

    def random_numbers_range(self, min_val, max_val, sigma_percentage=0.05):
        """ Function generating an random number in a given range of min_val and max_val. Distribution is more or less
            gaussian. When a generated random number is below min_val, min_val will be returned, if the number is above
            max_val, max_val will be returned.

         Parameters:
            min_val (dbl): upper boundary of random number range
            max_val (dbl): lower boundary of random number range
            sigma_percentage (dbl), optional: sets the percentage of mean to be used as sigma.
            Has to be between 0 and 1.

        Returns:
            double
        """

        try:
            mu_val = (min_val+max_val)/2
            # If sigma_val is 0, the result of random.gauss equals mu_val. Therefore it will be added 0.01.
            sigma_val = mu_val * sigma_percentage + 0.01

            # Generating the random number
            random_number = min(max_val, max(min_val, random.gauss(mu_val, sigma_val)))
            return random_number

        except Exception as err:
            self.log.error(f'An error occurred {err}')
            raise Exception

    def get_random_data_set(self, input_data, maximum, plot: bool = False):
        """ Creates a ndarray of the size of the original data set filled with random numbers. Random numbers
            boundaries are defined by the min/max-values of the given data set influenced by the given offset.

        Parameters:
            input_data (list, dict): input data as type(list or dict) containing the data that shall analysed
            maximum (dbl): sets the maximum deviation in percentage to the given data set.
            plot (bool): if true a histogram of the given data set and the output will be plotted

        Returns:
            ndarray
        """

        try:
            self.log.debug('Analysing statistics')
            keys = []

            if isinstance(input_data, dict):
                data_set = list(input_data.values())
                keys = list(input_data.keys())
            elif isinstance(input_data, list):
                if len(input_data[0] == 1):
                    data_set = input_data
                else:
                    self.log.error('Input_data is list with more than one dimension.')
                    raise TypeError
            else:
                self.log.error('Input_data has to be of type dict or list(1-dimensional)')
                raise TypeError

            # Statistics of given data set
            min_val = min(data_set)
            max_val = max(data_set)
            mean_val = statistics.mean(data_set)
            stddev_val = statistics.stdev(data_set)
            coeff_of_var_val = stddev_val / mean_val + 0.01  # Will be used as input for the range of random numbers

            self.log.debug(f'Statistics of input:')
            self.log.debug(f'Minimum: {min_val}')
            self.log.debug(f'Maximum: {max_val}')
            self.log.debug(f'Mean: {mean_val}')
            self.log.debug(f'Standard deviation: {stddev_val}')
            self.log.debug(f'Coefficient of variation: {coeff_of_var_val}')

            # Influencing the statistics of the given data set depending on the given maximum percentage of deviation
            min_val_off = 1
            max_val_off = 1+maximum

            # Swap numbers if min is bigger then max
            if min_val_off > max_val_off:
                min_val_off, max_val_off = max_val_off, min_val_off

            # Creating an empty ndarray of the same size as given input data set
            rand_array = numpy.empty_like(data_set).astype(float)

            # Filling the random array with random numbers
            with numpy.nditer(rand_array, op_flags=['readwrite']) as it:
                for x in it:
                    random_no = self.random_numbers_range(min_val_off, max_val_off, coeff_of_var_val)
                    x[...] = random_no

            rand_array = numpy.multiply(rand_array, data_set)

            # Statistics of given data set
            min_val_rand = min(rand_array)
            max_val_rand = max(rand_array)
            mean_val_rand = statistics.mean(rand_array)
            stddev_val_rand = statistics.stdev(rand_array)
            # coeff_of_var_val_rand will be used as input for the range of random numbers
            coeff_of_var_val_rand = stddev_val_rand/mean_val_rand

            self.log.debug('Statistics of output:')
            self.log.debug(f'Minimum: {min_val_rand}')
            self.log.debug(f'Maximum: {max_val_rand}')
            self.log.debug(f'Mean: {mean_val_rand}')
            self.log.debug(f'Standard deviation: {stddev_val_rand}')
            self.log.debug(f'Coefficient of variation: {coeff_of_var_val_rand}')

            # printing output for debugging purposes
            if plot:
                fig = plt.figure()
                sub1 = fig.add_subplot(121)
                sub1.hist(data_set, bins='auto', range=(min_val, max_val))
                sub1.set_title('Histogram input data set')

                sub2 = fig.add_subplot(122)
                sub2.hist(rand_array, bins='auto', range=(min_val_rand, max_val_rand))
                sub2.set_title('Histogram random numbers')
                plt.show()

            if isinstance(input_data, dict):
                output_data = {}

                if len(rand_array) == len(keys):
                    for i in range(len(rand_array)):
                        output_data[keys[i]] = rand_array[i]

                else:
                    self.log.error(f'Dimensions of randomized data len(rand_array)={len(rand_array)} and dictionary'
                                   f'keys len(keys)={len(keys)} do not fit, have to be equal.')
                    raise ValueError

            elif isinstance(input_data, list):
                output_data = rand_array

            else:
                return []

            return output_data

        except Exception as err:
            self.log.error(f'An error occurred {err}')
            raise Exception
