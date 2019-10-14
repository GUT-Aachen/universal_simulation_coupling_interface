import random


def random_numbers_range(min_val, max_val, sigma_percentage = 0.1):
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

    return min(max_val, max(min_val, random.gauss(mu_val, sigma_val)))


for x in range(10):
    num = random_numbers_range(0.25,0.3)
    print(num)
