import request_data as rd
import pytest
import os

def test_load_house_data():
    url = r'https://www.hemnet.se/salda/villa-5rum-marstrand-kungalvs-kommun-klaveron-580-718649'
    rd.load_house_data(url)

def test_get_data(tmpdir):

    file_path = os.path.join(str(tmpdir),'test.csv')
    rd.get_data(file_path,i_max = 1)

def test_get_data_append(tmpdir):

    file_path = os.path.join(str(tmpdir),'test.csv')
    rd.get_data(file_path,i_max = 1)

    file_path = os.path.join(str(tmpdir), 'test.csv')
    rd.get_data(file_path, i_max=1)