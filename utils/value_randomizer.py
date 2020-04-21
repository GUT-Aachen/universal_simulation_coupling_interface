import random
import statistics
import numpy

import matplotlib.pyplot as plt  # used for visualisation of transformation validation


def random_numbers_range(min_val, max_val, sigma_percentage = 0.05):
    """ Function generating an random number in a given range of min_val and max_val. Distribution is more or less
        gaussian. When a generated random number is below min_val, min_val will be returned, if the number is above
        max_val, max_val will be returned.
     Parameters:
        min_val (dbl): upper boundary of random number range
        max_val (dbl): lower boundary of random number range
        sigma_percentage (dbl), optional: sets the percentage of mean to be used as sigma. Has to be between 0 and 1.
    Returns:
        double
    """
    mu_val = (min_val+max_val)/2
    sigma_val = mu_val * sigma_percentage

    # Generating the random number
    random_number = min(max_val, max(min_val, random.gauss(mu_val, sigma_val)))

    return random_number


def get_random_dataset(dataset, maximum, plot = False):
    """ Creates a ndarray of the size of the original dataset filled with random numbers. Random numbers boundaries are
        defined by the min/max-values of the given dataset influenced by the given offset.
    Parameters:
        dataset (ndarray): input data as type(narray) containing the data that shall analysed
        maximum (dbl): sets the maximum deviation in percentage to the given dataset.
        plot (bool): if true a histogram of the given dataset and the output will be plotted
    Returns:
        ndarray
    """

    function_name = 'get_random_dataset'
    print_pre_str = '\t' + function_name + ' >> '
    print('* Start function: ', function_name)
    print(print_pre_str, '* Analysing statistics')

    # Statistics of given dataset
    min_val = min(dataset)
    max_val = max(dataset)
    mean_val = statistics.mean(dataset)
    stdev_val = statistics.stdev(dataset)
    coeff_of_var_val = stdev_val/mean_val # Will be used as input for the range of random numbers

    print(print_pre_str, '* Statistics of input')
    print(print_pre_str, '\t Minimum: \t\t\t\t', str(min_val))
    print(print_pre_str, '\t Maximum: \t\t\t\t', str(max_val))
    print(print_pre_str, '\t Mean: \t\t\t\t\t', str(mean_val))
    print(print_pre_str, '\t Standard deviation: \t', str(stdev_val))
    print(print_pre_str, '\t Coefficient of variation: \t', str(coeff_of_var_val))

    # Influencing the statistics of the given dataset depending on the given maximum percentage of deviation
    min_val_off = 1
    max_val_off = 1+maximum

    # Swap numbers if min is bigger then max
    if min_val_off > max_val_off:
        min_val_off, max_val_off = max_val_off, min_val_off

    # Creating an empty ndarray of the same size as given input dataset
    rand_array = numpy.empty_like(dataset)

    # Filling the random array with random numbers
    with numpy.nditer(rand_array, op_flags=['readwrite']) as it:
        for x in it:
            random_no = random_numbers_range(min_val_off, max_val_off, coeff_of_var_val)
            x[...] = random_no

    rand_array = numpy.multiply(rand_array, dataset)

    # Statistics of given dataset
    min_val_rand = min(rand_array)
    max_val_rand = max(rand_array)
    mean_val_rand = statistics.mean(rand_array)
    stdev_val_rand = statistics.stdev(rand_array)
    coeff_of_var_val_rand = stdev_val_rand/mean_val_rand # Will be used as input for the range of random numbers

    print(print_pre_str, '* Statistics of output')
    print(print_pre_str, '\t Minimum: \t\t\t\t', str(min_val_rand))
    print(print_pre_str, '\t Maximum: \t\t\t\t', str(max_val_rand))
    print(print_pre_str, '\t Mean: \t\t\t\t\t', str(mean_val_rand))
    print(print_pre_str, '\t Standard deviation: \t', str(stdev_val_rand))
    print(print_pre_str, '\t Coefficient of variation: \t', str(coeff_of_var_val_rand))

    # printing output for debugging purposes
    if plot:
        fig = plt.figure()
        sub1 = fig.add_subplot(121)
        sub1.hist(dataset, bins='auto', range=(min_val, max_val))
        sub1.set_title('Histrogram input dataset')

        sub2 = fig.add_subplot(122)
        sub2.hist(rand_array, bins='auto', range=(min_val_rand, max_val_rand))
        sub2.set_title('Histrogram random numbers')
        plt.show()

    print(print_pre_str, 'exiting function')
    print()

    return rand_array
