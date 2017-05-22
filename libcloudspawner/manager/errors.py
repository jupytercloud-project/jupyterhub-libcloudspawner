#!/usr/bin/env python
# _*_ coding : utf-8 _*_

""" CloudManager errors with cloud
"""

__author__ = "Tristan Le Toullec"
__copyright__ = "Copyright 2017, LOPS"
__credits__ = ["Tristan Le Toullec"]
__license__ = "CeCILL-B"
__maintainer__ = "Tristan Le Toullec"
__email__ = "tristan.letoullec@cnrs.fr"


class ImageNotFoundError(Exception):
    """ This exception was raised in case requested image \
    was not found by cloud driver
    """

    def __init__(self):
        self.message="Notebook template not found, \
        please contact JupyterHub admin team"

    def __str__(self):
        return str(self.message)



class NetworkNotFoundError(Exception):
    """ This exception was raised in case network was not found by cloud driver
    """

    def __init__(self):
        self.message="Notebook network not available, \
        please contact JupyterHub admin team"

    def __str__(self):
        return str(self.message)


class SizeNotFoundError(Exception):
    """ This exception was raised in case size/flavor was not found by cloud driver
    """

    def __init__(self):
        self.message="Notebook size not exist or not available for you, \
        please contact JupyterHub admin team"

    def __str__(self):
        return str(self.message)

