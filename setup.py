import os
os.system("python py_aseprite-master/setup.py install")


from distutils.core import setup


setup(
    name='aseprite_to_fetch_parser',
    version='1',
    packages=['aseprite_to_fetch_parser',],
    license='MIT'
)
import glob

os.system("cp save_as_fetch.lua $HOME/.config/aseprite/scripts/")
if not glob.glob("/home/*/Documents/aseprite_to_fetch_parser/fetch_animations"):
    os.system("mkdir $HOME/Documents/aseprite_to_fetch_parser/fetch_animations")