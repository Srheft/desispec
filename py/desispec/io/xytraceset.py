"""
desispec.io.xytraceset
=================

I/O routines for XYTraceSet objects
"""


import os.path
import numpy as np
from astropy.io import fits

from ..xytraceset import XYTraceSet
from desiutil.log import get_logger

def _traceset_from_image(wavemin,wavemax,hdu,label=None) :
    log=get_logger()
    head=hdu.header
    extname=head["EXTNAME"]
    if wavemin is not None :
        if abs(head["WAVEMIN"]-wavemin)>0.001 :
            mess="WAVEMIN not matching in hdu {} {}!={}".format(extname,head["WAVEMIN"],wavemin)
            log.error(mess)
            raise ValueError(mess)
    else :
        wavemin=head["WAVEMIN"]
    if wavemax is not None :
        if abs(head["WAVEMAX"]-wavemax)>0.001 :
            mess="WAVEMAX not matching in hdu {} {}!={}".format(extname,head["WAVEMAX"],wavemax)
            log.error(mess)
            raise ValueError(mess)
    else :
        wavemax=head["WAVEMAX"]
    if label is not None :
        log.info("read {} from hdu {}".format(label,extname))
    else :
        log.info("read coefficients from hdu {}".format(label,extname))
                
    return hdu.data,wavemin,wavemax 

def _traceset_from_table(wavemin,wavemax,hdu,pname) :
    log=get_logger()
    head=hdu.header
    table=hdu.data
    
    extname=head["EXTNAME"]
    i=np.where(table["PARAM"]==pname)[0][0]

    if "WAVEMIN" in table.dtype.names :
        twavemin=table["WAVEMIN"][i]
        if wavemin is not None :
            if abs(twavemin-wavemin)>0.001 :
                mess="WAVEMIN not matching in hdu {} {}!={}".format(extname,twavemin,wavemin)
                log.error(mess)
                raise ValueError(mess)
        else :
            wavemin=twavemin
    
    if "WAVEMAX" in table.dtype.names :
        twavemax=table["WAVEMAX"][i]
        if wavemax is not None :
            if abs(twavemax-wavemax)>0.001 :
                mess="WAVEMAX not matching in hdu {} {}!={}".format(extname,twavemax,wavemax)
                log.error(mess)
                raise ValueError(mess)
        else :
            wavemax=twavemax
    
    log.info("read {} from hdu {}".format(pname,extname))
    return table["COEFF"][i],wavemin,wavemax 

def read_xytraceset(filename) :
    """
    Reads traces in PSF fits file
    
    Args:
        filename : Path to input fits file which has to contain XTRACE and YTRACE HDUs
    Returns:
         XYTraceSet object
    
    """

    log=get_logger()

    
    xcoef=None
    ycoef=None
    xsigcoef=None
    ysigcoef=None
    wavemin=None
    wavemax=None
     
    
    fits_file = fits.open(filename)
    
    
    # npix_y, needed for boxcar extractions
    npix_y=0
    for hdu in [0,"XTRACE","PSF"] :
        if npix_y > 0 : break
        if hdu in fits_file : 
            head = fits_file[hdu].header
            if "NPIX_Y" in head :
                npix_y=int(head["NPIX_Y"])
    if npix_y == 0 :
        raise KeyError("Didn't find head entry NPIX_Y in hdu 0, XTRACE or PSF")
    log.info("npix_y={}".format(npix_y))
    
    try :
        psftype=fits_file[0].header["PSFTYPE"]
    except KeyError :
        psftype=""
    
    # now read trace coefficients
    log.info("psf is a '%s'"%psftype)
    if psftype == "bootcalib" :
        xcoef,wavemin,wavemax =_traceset_from_image(wavemin,wavemax,fits_file[0],"xcoef")
        ycoef,wavemin,wavemax =_traceset_from_image(wavemin,wavemax,fits_file[1],"ycoef")
    else :
        for k in ["XTRACE","XCOEF","XCOEFF"] :
            if k in fits_file :
                xcoef,wavemin,wavemax =_traceset_from_image(wavemin,wavemax,fits_file[k],"xcoef")
        for k in ["YTRACE","YCOEF","YCOEFF"] :
            if k in fits_file :
                ycoef,wavemin,wavemax =_traceset_from_image(wavemin,wavemax,fits_file[k],"ycoef")
        for k in ["XSIG"] :
            if k in fits_file :
                xsigcoef,wavemin,wavemax =_traceset_from_image(wavemin,wavemax,fits_file[k],"xsigcoef")
        for k in ["YSIG"] :
            if k in fits_file :
                ysigcoef,wavemin,wavemax =_traceset_from_image(wavemin,wavemax,fits_file[k],"ysigcoef")
    
    if psftype == "GAUSS-HERMITE" : # older version where XTRACE and YTRACE are not saved in separate HDUs
        hdu=fits_file["PSF"]
        if xcoef is None    : xcoef,wavemin,wavemax =_traceset_from_table(wavemin,wavemax,hdu,"X")
        if ycoef is None    : ycoef,wavemin,wavemax =_traceset_from_table(wavemin,wavemax,hdu,"Y")
        if xsigcoef is None : xsigcoef,wavemin,wavemax =_traceset_from_table(wavemin,wavemax,hdu,"GHSIGX")
        if ysigcoef is None : ysigcoef,wavemin,wavemax =_traceset_from_table(wavemin,wavemax,hdu,"GHSIGY")
    
    log.info("wavemin={} wavemax={}".format(wavemin,wavemax))
    
    if xcoef is None or ycoef is None :
        raise ValueError("could not find xcoef and ycoef in psf file %s"%filename)
    
    if xcoef.shape[0] != ycoef.shape[0] :
        raise ValueError("XCOEF and YCOEF don't have same number of fibers %d %d"%(xcoef.shape[0],ycoef.shape[0]))
    
    fits_file.close()
    
    return XYTraceSet(xcoef,ycoef,wavemin,wavemax,npix_y,xsigcoef=xsigcoef,ysigcoef=ysigcoef)

   
   
