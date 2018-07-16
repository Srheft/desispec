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


def read_xytraceset(filename) :
    """
    Reads traces in PSF fits file
    
    Args:
        filename : Path to input fits file which has to contain XTRACE and YTRACE HDUs
    Returns:
        xtrace : 2D np.array of shape (nfibers,ncoef) containing Legendre coefficents for each fiber to convert wavelenght to XCCD
        ytrace : 2D np.array of shape (nfibers,ncoef) containing Legendre coefficents for each fiber to convert wavelenght to YCCD
        wavemin : float
        wavemax : float. wavemin and wavemax are used to define a reduced variable legx(wave,wavemin,wavemax)=2*(wave-wavemin)/(wavemax-wavemin)-1
                  used to compute the traces, xccd=legval(legx(wave,wavemin,wavemax),xtrace[fiber])
    
    """

    log=get_logger()

    
    xtrace=None
    ytrace=None
    wavemin=None
    wavemax=None
    wavemin2=None
    wavemax2=None
    
    
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
        head =fits_file[0].header
        wavemin = head["WAVEMIN"]
        wavemax = head["WAVEMAX"]
        xcoef   = fits_file[0].data
        ycoef   = fits_file[1].data        
        wavemin2 = wavemin
        wavemax2 = wavemax
    elif "XTRACE" in fits_file :
        xtrace=fits_file["XTRACE"].data
        ytrace=fits_file["YTRACE"].data
        wavemin=fits_file["XTRACE"].header["WAVEMIN"]
        wavemax=fits_file["XTRACE"].header["WAVEMAX"]
        wavemin2=fits_file["YTRACE"].header["WAVEMIN"]
        wavemax2=fits_file["YTRACE"].header["WAVEMAX"]
    elif psftype == "GAUSS-HERMITE" : # older version where XTRACE and YTRACE are not saved in separate HDUs
        table=fits_file["PSF"].data        
        i=np.where(table["PARAM"]=="X")[0][0]
        wavemin=table["WAVEMIN"][i]
        wavemax=table["WAVEMAX"][i]
        xtrace=table["COEFF"][i]
        i=np.where(table["PARAM"]=="Y")[0][0]
        ytrace=table["COEFF"][i]
        wavemin2=table["WAVEMIN"][i]
        wavemax2=table["WAVEMAX"][i]
    
    if xtrace is None or ytrace is None :
        raise ValueError("could not find xtrace and ytrace in psf file %s"%filename)
    if wavemin != wavemin2 :
        raise ValueError("XTRACE and YTRACE don't have same WAVEMIN %f %f"%(wavemin,wavemin2))
    if wavemax != wavemax2 :
        raise ValueError("XTRACE and YTRACE don't have same WAVEMAX %f %f"%(wavemax,wavemax2))
    if xtrace.shape[0] != ytrace.shape[0] :
        raise ValueError("XTRACE and YTRACE don't have same number of fibers %d %d"%(xtrace.shape[0],ytrace.shape[0]))
    
    fits_file.close()
    
    return XYTraceSet(xtrace,ytrace,wavemin,wavemax,npix_y)

   
   