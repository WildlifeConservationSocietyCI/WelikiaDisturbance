import numpy as np

def tree_height(params, A, S):
    """
    tree height formula
    reference: 'Site Index Curves for Forest Tree Species in the Eastern United States'
    Carmean et al. 1989

    H = tree height (ft)
    A = age
    S = site index
    bi = model parameters

    :param params:
    :param A:
    :param S:
    :return:
    """
    b1 = params["b1"]
    b2 = params["b2"]
    b3 = params["b3"]
    b4 = params["b4"]
    b5 = params["b5"]

    H = b1 * S**b2 * (1 - np.exp(b3 * A)**(b4 * S**b5))
    return H

def DBH_bean(A):
    """
    logarithmic age DBH relationship for red oak
    reference: 'Using a spatially explicit ecological model to test scenarios
    of fire use by Native Americans: An example from the Harlem Plains, New York, NY'
    Bean and Sanderson 2007

    DBH = Diameter at Breast Height (in)
    A = age

    :param A:
    :return:
    """

    DBH = 25.706 * ( np.log(A) ) - 85.383
    return DBH

def DBH_eq_3_loewenstein(A):
    """
    linear DBH age relationship for red oak [equation 3]
    reference : 'Age and diameter structure of a managed uneven-aged oak forest'
    Loewenstein et al. 2000

    DBH = Diameter at Breast Height (cm)
    A = age

    :param A:
    :return:
    """

    DBH = (A - 36.329) / 0.919
    return DBH

def DBH_eq_2_loewenstein(A):
    """
    linear DBH age relationship for red oak [equation 2]
    reference : 'Age and diameter structure of a managed uneven-aged oak forest'
    Loewenstein et al. 2000

    DBH = Diameter at Breast Height (cm)
    A = age

    :param A:
    :return:
    """

    DBH = (A - 34.44) / 1.18
    return DBH


shape = (3, 3)
age = np.random.randint(0, 15, size=shape)

print age

p = {'b1': 6.1785,
     'b2': 0.6619,
     'b3': -0.0241,
     'b4': 25.0185,
     'b5': -0.74}
