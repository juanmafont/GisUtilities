#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

    Class to work with heatmaps over layer with features type : Point, LinesString or Polygon
    This class put/add two field called 'tiffvalue' and 'lengthValue" or whatever user select, into every feature. 
    The value of "tiffValue" field will come from the same features's coordinates but from a geotiff file,
    the geotiff file can has different size that the origin vector layer and could not cover all the extend, 
    in that case the value "returned" from that geotiff's positions will be '-9999'
    If topology is a line, then the final calculate value will be the mediam of every vertex of the full line
    The value of "lengthValue" will be the length of every linestring feature

"""

import progressbar
from osgeo import gdal,ogr
from gdalconst import * 

debug = False

class MaskHeatmap:

    """ Mask a feature with values from an heatmap

     Attributes:
        nameVector   (string) : Name of the vector file with features to 'mask'
        heatmap      (string) : Name of the file that contain the geotiff
        fieldNameA   (string) : Name of the field to add/update into feature's file as 'tiffValue'.
        fieldNameB   (string) : Name of the field to add/update into feature's file as 'length'.
        noUpdate     (boolean): If true, features out of heatmap will not be update (default will be set with -9999 vaue), you can
                                relaunch this script covering different zones.
    """   
            
    def __init__( self, _nameVector, _heatmap, _fieldNameA='tiffvalue', _fieldNameB="length", _noUpdate=False ):
    
        self.nameVector = _nameVector
        self.heatmap = _heatmap
        self.fieldNameA = _fieldNameA
        self.fieldNameB = _fieldNameB
        self.noUpdate = _noUpdate
        
        self.__openVector()
        self.__openRaster()
        self.__doMask()
        
    def __openVector( self ): 
        
        # Open a vector file, and get field names
        
        self._vector = ogr.Open( self.nameVector, update=True )
        self._layer = self._vector.GetLayer()
        self._layer_defn = self._layer.GetLayerDefn()
  
        self.__addField( self.fieldNameA ); 
        self.__addField( self.fieldNameB ); 
   
    def __addField( self, _fieldName ):
   
        self._listFields = [ self._layer_defn.GetFieldDefn( i ).GetName() for i in range( self._layer_defn.GetFieldCount() ) ]
        
        print "Total fields in file:",len( self._listFields )
        if _fieldName in self._listFields:
            print "Field '%s' detected in '%s'" % ( _fieldName, self.nameVector )
        else:
            print "Field '%s' added to '%s'" % ( _fieldName, self.nameVector )
            # Add a new field
            self._new_field = ogr.FieldDefn( _fieldName, ogr.OFTInteger )
            self._layer.CreateField( self._new_field )

        
    def __openRaster( self ): 
       
        print "Reading/Loading geotiff file." 
        #open raster file
        self._src_ds = gdal.Open( self.heatmap, GA_ReadOnly ) 
        self._gt = self._src_ds.GetGeoTransform()
        self._rb = self._src_ds.GetRasterBand( 1 )
        
        gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid
    
        self._cols  = self._src_ds.RasterXSize
        self._rows  = self._src_ds.RasterYSize
        self._bands = self._src_ds.RasterCount
        self._band  = self._src_ds.GetRasterBand( 1 )
      
        if debug:
            print "Source raw cols:", self._cols
            print "Source raw rows:", self._rows
            print "Source raw bands:",self._bands
          
        # Read full raster file into array
        self._data = self._band.ReadAsArray( 0, 0, self._cols, self._rows )

    def __doMask( self ):        
    
        # TODO check if geometry are categorized like simple or multiple
        self._geomType= self._layer.GetGeomType()
      
        
        if  self._geomType == ogr.wkbPolygon or self._geomType == ogr.wkbPoint: # More fast when geom has Centroids
            self.__fillMask( False )
        elif self._geomType ==  ogr.wkbLineString: # More slow, when geom has not real Centroid's
            self.__fillMask( True )
        else:
             sys.exit("ERROR: Geometry needs to be either Polygon, LineString or Point")   
    
    def __fillMask( self, _isLine=False ):        
                         
        self._cntFeat = len( self._layer )
        print "Updating %i features using values from the heatmap mask tiff file '%s'" % ( self._cntFeat, self.heatmap )
        
        self._bar = self.__doProgress( self._cntFeat )                   
        self._bar.start()
        self._cnt = -1    
        for feat in self._layer:
            self._cnt += 1
            geom = feat.GetGeometryRef()      

            wasOut = False
            # Some features has not geometry (is empty, or invalid )
            if geom.IsValid():
                
                # Remember, geom could be a geom LINE
                if _isLine: # Must save percent length between vertex into black zone 
                    lengthInBlack=0
                    lengthInWhite=0
                    val = -9999
                    length = 0        
                    np = geom.GetPointCount()
                    if np > 0: 
                        for p in xrange( np - 1 ):
                            p1 = ogr.Geometry( ogr.wkbPoint )
                            p2 = ogr.Geometry( ogr.wkbPoint )
                            p1x, p1y, p1z = geom.GetPoint( p )
                            p2x, p2y, p2z = geom.GetPoint( p + 1 )
                            p1.AddPoint( p1x, p1y )
                            p2.AddPoint( p2x, p2y )
                            d = p1.Distance( p2 )
                            # TODO: If distance > 200 then create virtual intermediate points (till distance less than 200)
                            v1 = self.__getValueTiff( p1x, p1y )
                            v2 = self.__getValueTiff( p2x, p2y )
                            # Beware,maybe point outside extend
                            if v1 == -9999 or v2 == -9999:
                                wasOut = True
                            else:
                                if v1 == 255 and v2 == 255:# Whitezone 
                                   lengthInWhite += d
                                else:  # Black zone or transition (black/white) zone       
                                    lengthInBlack += d

                        length = lengthInWhite + lengthInBlack
                        try:               
                            val = int( lengthInBlack * 100 / length )
                        except:
                            val = -9999       
 
                else:
                    mx=geom.Centroid().GetX()
                    my=geom.Centroid().GetY()
                    val = self.__getValueTiff( mx, my )
                    if val == -9999:
                        wasOut = True

                """
                raster GeoTransform
                [0] top left x 
                [1] w-e pixel resolution 
                [2]  0
                [3] top left y 
                [4]  0 
                [5] n-s pixel resolution (negative value) 
                """
            # Update only    
            if not self.noUpdate or ( self.noUpdate and not wasOut ):    
                feat.SetField( self.fieldNameA, val )
                feat.SetField( self.fieldNameB, length )
            self._layer.SetFeature( feat )
            self._bar.update( self._cnt )
                
        self._bar.finish()  
        # Unset dataSources to update
        self._src_ds=None
        self._vector=None
       
    def __getValueTiff( self, _mx, _my ):
              
        self._px = int( ( _mx - self._gt[ 0 ] ) / self._gt[ 1 ] ) #x pixel
        self._py = int( ( _my - self._gt[ 3 ] ) / self._gt[ 5 ] ) #y pixel
        if debug:
            print "px: %i py: %i" % ( self._px, self._py )
            print "mx: %f my: %f" % ( _mx, _my )
            print "origX: %f" % ( self._gt[ 0 ] )
            print "origY: %f" % ( self._gt[ 3 ] )
            print "Size pixel: %f %f" %( self._gt[ 1 ], self._gt[ 5 ] )
            

        try: #in case raster isnt full extent
            #structval=rb.ReadRaster(px,py,1,1,buf_type=gdal.GDT_Float32) #Assumes 32 bit int- 'float'
            #intval = struct.unpack('f' , structval) #assume float
            #val=intval[0]
            val = int( self._data[ self._py, self._px ] )
        except:
            val = -9999 #or some value to indicate a fail

        return val    
    
    def __doProgress( self, _maxValue ):

        self._bar = progressbar.ProgressBar( maxval = _maxValue, widgets=[ progressbar.Bar( '=', '[', ']' ), ' ', progressbar.Percentage() ] )
        return self._bar
