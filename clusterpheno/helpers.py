#!usr/bin/env python
import sys, os, re
import numpy as np
import pandas as pd
import itertools as it
import contextlib
sys.path.insert(0,'/extra/huayangs/work/untangle')
sys.path.insert(0,'/extra/huayangs/work/pathos')
sys.path.insert(0,'/extra/huayangs/work/tqdm')
import untangle
from tqdm import tqdm
from pathos.multiprocessing import ProcessingPool as Pool

class Counter:
    def __init__(self, counter_object):
        cdata = counter_object.cdata.split('\n')
        self.name = cdata[1].split('\"')[1]
        self.nevents = int(cdata[2].split(' ')[0])
""" Some helper functions. """

def convert_SAF_to_XML(filename):
    """ Converts a SAF file to XML """

    def convert_to_XML_line(line):
        """ Converts a SAF  line to XML """
        line = line.replace(' < ', ' &lt; ')
        line = line.replace(' > ', ' &gt; ')
        if line.startswith('#'):
            line = '<!-- '+line.rstrip()+' -->\n'
        return line

    with open(filename, 'r') as f:
        result = [convert_to_XML_line(line) for line in f]

    xml_filename = filename.split('.')[0]+'.xml'

    with open(xml_filename, 'w') as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<root>\n')
        for line in result:
            f.write(line)
        f.write('</root>\n')

def get_SAF_objects(filename):
    """ Get SAF objects from a file. """
    convert_SAF_to_XML(filename+'.saf')
    xml_filepath = filename+'.xml'
    return (untangle.parse(xml_filepath)).root

def modify_file(filepath, line_modification_function):
    """ Modify a file in place.

    Parameters
    ----------

    filepath: str
        Path to the file to be modified.
    line_modification_function: func
        The line modification function. Takes one parameter, the line, and
        returns either the original line or a modified version of it.
    """

    with open(filepath, 'r') as f:
        lines = [line_modification_function(line) for line in f.readlines()]
    with open(filepath, 'w') as f: [f.write(line) for line in lines]

def do_parallel(function, list, ncores = 28):
    p = Pool(ncores)
    for _ in tqdm(p.uimap(function, list), total = len(list)):
        pass

def _change_directory(destination_directory):
    cwd = os.getcwd()
    os.chdir(destination_directory)
    try: yield
    except: pass
    finally: os.chdir(cwd)

cd = contextlib.contextmanager(_change_directory)
""" A context manager to handle temporary directory changes.

    Example
    --------
    Here is an example of how one might use the function::

        with cd('relative/path/to/directory'):
            print(os.getcwd()) # Prints the working directory
            subprocess.call('./run_external_program') # Runs some non-python program

    Parameters
    ----------
    destination_directory : string
        The directory to temporarily change the working directory to.

    """
