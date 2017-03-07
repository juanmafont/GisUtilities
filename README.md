# tiffvalue.py

This python script will put/add a field called 'tiffvalue' or whatever user select, into every feature. The value of this field will come from the same features's coordinates but from a geotiff file, the geotiff file can has different size that the origin vector layer and could not cover all the extend, in that case the value "returned" from that geotiff's positions will be '-9999' or not update (see argument -n ). The value will be the percent of his length over the black zone into the mask file (geotiff). This python script also add a field called 'length'

This python script need the python class HeatMap.py, so you must download it and put into same directory,  remember to create and empty file called '__init__.py' also, python need it.

# Use

tiffvalue.py -hm mask.tiff sourceB-splitted.shp

# Requisites

python-progressbar -> http://code.google.com/p/python-progressbar/
python-gdal 

How to install into Ubuntu (using ppa ubuntugis-stable or ubuntugis-unstable)
( https://launchpad.net/~ubuntugis/+archive/ubuntu/ppa )

sudo apt install gdal-bin python-gdal python-progressbar
