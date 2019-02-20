import numpy as np
import pandas as pd
import settings as s

"""
site index curve parameters
reference: 'Site Index Curves for Forest Tree Species in the Eastern United States'
Carmean et al. 1989
"""

site_index_parameters = pd.read_csv(s.SITE_INDEX_PARAMETERS, index_col=0)
coeffecients = pd.read_csv(s.COEFFECIENTS, index_col=0)


def tree_height_carmean(key, age, site_index):
    """
    tree height formula
    reference: 'Site Index Curves for Forest Tree Species in the Eastern United States'
    Carmean et al. 1989

    H = tree height (ft)
    A = age
    S = site index
    bi = model parameters

    :param key:
    :param age:
    :param site_index:
    :return:
    """

    b1 = site_index_parameters.ix[key]["b1"]
    b2 = site_index_parameters.ix[key]["b2"]
    b3 = site_index_parameters.ix[key]["b3"]
    b4 = site_index_parameters.ix[key]["b4"]
    b5 = site_index_parameters.ix[key]["b5"]

    height = b1 * site_index ** b2 * (1 - np.exp(b3 * age) ** (b4 * site_index ** b5))
    return height


def tree_height_bean(age):
    """
    logarithmic age-height relationship for red oak
    reference: 'Using a spatially explicit ecological model to test scenarios
    of fire use by Native Americans: An example from the Harlem Plains, New York, NY'
    Bean and Sanderson 2007

    height = tree height (ft)
    A = age

    :param age:
    :return:
    """

    height = 44 * np.ma.log(age) - 93

    return height


def dbh_bean(age):
    """
    logarithmic age dbh relationship for red oak
    reference: 'Using a spatially explicit ecological model to test scenarios
    of fire use by Native Americans: An example from the Harlem Plains, New York, NY'
    Bean and Sanderson 2007

    dbh = Diameter at Breast Height (in)
    A = age

    :param age:
    :return:
    """

    # ma.log takes log of values greater than 0
    dbh = 25.706 * np.ma.log(age) - 85.383

    return dbh


def dbh_eq_3_loewenstein(age):
    """
    linear dbh age relationship for red oak [equation 3]
    reference : 'Age and diameter structure of a managed uneven-aged oak forest'
    Loewenstein et al. 2000

    dbh = Diameter at Breast Height (cm)
    A = age

    :param age:
    :return:
    """

    dbh = (age - 36.329) / 0.919
    return dbh


def dbh_eq_2_loewenstein(age):
    """
    linear dbh age relationship for red oak [equation 2]
    reference : 'Age and diameter structure of a managed uneven-aged oak forest'
    Loewenstein et al. 2000

    dbh = Diameter at Breast Height (cm)
    A = age

    :param age:
    :return:
    """

    dbh = (age - 34.44) / 1.18
    return dbh


def get_potbag(species, dbh, site_index):
    """
    potential basal area growth
    reference: Individual-Tree Diameter Growth Model for Northeastern U.S.
    Teck and Hilt 1990

    POTBAG = potential basal area growth
    DBH = diameter at brest height
    SI = site index

    :param species:
    :param dbh:
    :param site_index:
    :return: potbag:
    """

    b1 = coeffecients.ix[species].b1
    b2 = coeffecients.ix[species].b2

    potbag = b1 * site_index * (1.0 - np.exp(-b2 * dbh * 10))

    return potbag


def get_bag(species, dbh, site_index):
    """
    limit basal area growth by competition
    reference: Individual-Tree Diameter Growth Model for Northeastern U.S.
    Teck and Hilt 1990

    DBH = diameter at brest height
    SI = site index
    bal = basal area of trees larger than or equal to subject tree

    :param species:
    :param dbh:
    :param site_index:
    :return: bag:
    """
    b3 = coeffecients.ix[species].b3
    bal = coeffecients.ix[species].BAL

    potbag = get_potbag(species, dbh, site_index)
    bag = potbag * (np.exp(-b3 * bal))
    return bag


def get_dgrow(species, dbh, site_index):
    """
    convert basal area growth to diameter
    reference: Individual-Tree Diameter Growth Model for Northeastern U.S.
    Teck and Hilt 1990
    :param species:
    :param dbh:
    :param site_index:
    :return:
    """

    bag = get_bag(species, dbh, site_index)
    dgrow = (((0.00545415 * dbh ** 2) + bag) / 0.00545415) ** 0.5 - dbh

    return dgrow
