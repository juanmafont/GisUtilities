#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

    This script will put/add a field called 'tiffvale' or whatever user select, into every feature. 
    The value this field will come from the same features's coordinates but from a geotiff file,
    the geotiff file can has different size that the origin vector layer and could not cover all the extend, 
    in that case the value "returned" from that geotiff's positions will be '-9999' or not update (see argument -n )
    If topology is a line, then the final calculate value will be the mediam of every vertex of the full line

"""


import sys,argparse,os
from MaskHeatmap import MaskHeatmap
from osgeo import gdal,ogr
from gdalconst import * 

debug = False
noUpdate = False # If true then will not update features out heatmap extension (so you can apply succesives heatmaps for big zones)

def main(argv):

    global debug

    parser = argparse.ArgumentParser(argv[0]+' Put a integer value obtain from a heatmat into field, update if field exist ')
    parser.add_argument('inputfile', help='Name of input data file')
    parser.add_argument('-hm', help='Name of the heatmap input file', default='heatmap.tif')
    parser.add_argument('-f', help='Name of field to update/create', default='tiffvalue')
    parser.add_argument('-l', help='Name of field to update/create', default='length')    
    parser.add_argument('-n', help='Not update features out heatmap extension', action='store_true' )
    parser.add_argument('-d', help='Debug mode, show some information', action='store_true')   
   
    if len(argv) < 1:
        parser.print_help()
        # parser.print_usage() # for just the usage line
        parser.exit()
        exit(2)   
    
    # Arguments        
    args=parser.parse_args()
    inputfile=args.inputfile
    heatmap=args.hm
    fieldnameA=args.f
    fieldnameB=args.l
    debug=args.d    
             
    MaskHeatmap( inputfile, heatmap, fieldnameA, fieldnameB )

if __name__ == "__main__":
    main(sys.argv)

