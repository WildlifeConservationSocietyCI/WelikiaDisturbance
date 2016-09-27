import settings as s
import os
import numpy as np
import pandas as pd

"""
site index curve parameters
reference: 'Site Index Curves for Forest Tree Species in the Eastern United States'
Carmean et al. 1989
"""
site_index_parameters = pd.read_csv(os.path.join(s.ROOT_DIR, 'site_index_curve_table.csv'), index_col=0)


def tree_height_carmean(key, A, S):
    """
    tree height formula
    reference: 'Site Index Curves for Forest Tree Species in the Eastern United States'
    Carmean et al. 1989

    H = tree height (ft)
    A = age
    S = site index
    bi = model parameters

    :param key:
    :param A:
    :param S:
    :return:
    """

    b1 = site_index_parameters.ix[key]["b1"]
    b2 = site_index_parameters.ix[key]["b2"]
    b3 = site_index_parameters.ix[key]["b3"]
    b4 = site_index_parameters.ix[key]["b4"]
    b5 = site_index_parameters.ix[key]["b5"]

    H = b1 * S**b2 * (1 - np.exp(b3 * A)**(b4 * S**b5))
    return H


def tree_height_bean(A):
    """
    logarithmic age-height relationship for red oak
    reference: 'Using a spatially explicit ecological model to test scenarios
    of fire use by Native Americans: An example from the Harlem Plains, New York, NY'
    Bean and Sanderson 2007

    H = tree height (ft)
    A = age

    :param A:
    :return:
    """

    H = 44 * np.ma.log(A) - 93

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

    # ma.log takes log of values greater than 0
    DBH = 25.706 * np.ma.log(A) - 85.383

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


coeffecients = pd.read_csv(os.path.join(s.ROOT_DIR, 'basal_area_growth_coeffecients.csv'), index_col=0)

def POTBAG(species, DBH, SI):
    """
    potential basal area growth
    reference: Individual-Tree Diameter Growth Model for Northeastern U.S.
    Teck and Hilt 1990

    POTBAG = potential basal area growth
    DBH = diameter at brest height
    SI = site index

    :param species:
    :param DBH:
    :param SI:
    :return: potbag:
    """

    b1 = coeffecients.ix[species].b1
    b2 = coeffecients.ix[species].b2

    potbag = b1 * SI * (1.0 - np.exp(-b2 * DBH * 10))

    return potbag


def BAG(species, DBH, SI):
    """
    limit basal area growth by competition
    reference: Individual-Tree Diameter Growth Model for Northeastern U.S.
    Teck and Hilt 1990

    DBH = diameter at brest height
    SI = site index
    BAL = basal area of trees larger than or equal to subject tree

    :param species:
    :param DBH:
    :param SI:
    :return: bag:
    """
    b3 = coeffecients.ix[species].b3
    BAL = coeffecients.ix[species].BAL

    potbag = POTBAG(species, DBH, SI)
    bag = potbag * (np.exp(-b3 * BAL))
    return bag


def DGROW(species, DBH, SI):
    """
    convert basal area growth to diameter
    reference: Individual-Tree Diameter Growth Model for Northeastern U.S.
    Teck and Hilt 1990
    :param bag:
    :param dbh:
    :return:
    """

    bag = BAG(species, DBH, SI)
    dgrow = (((0.00545415 * DBH ** 2) + bag) / 0.00545415) ** 0.5 - DBH

    return dgrow