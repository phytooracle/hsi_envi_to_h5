#!/usr/bin/env python3
"""
Author : Emmanuel Gonzalez
Date   : 2021-06-04
Purpose: ENVI to H5 conversion of hyperspectral imagery. 
"""

import argparse
import os
import sys
import h5py
from spectral import * 
import numpy as np
import glob
import tempfile
import warnings
import pandas as pd
from datetime import datetime
import json
import glob
warnings.filterwarnings('ignore')


# --------------------------------------------------
def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Rock the Casbah',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('hdr_file',
                        metavar='hdr_file',
                        help='HDR file')

    parser.add_argument('-r',
                        '--rgb_outdir',
                        help='RGB output directory',
                        metavar='rgb_outdir',
                        type=str,
                        default='hsi_rgb_out')

    parser.add_argument('-h',
                        '--h5_outdir',
                        help='H5 output directory',
                        metavar='h5_outdir',
                        type=str,
                        default='hsi_h5_out')

    return parser.parse_args()


# --------------------------------------------------
def get_files(hdr_file):

    bin_file = hdr_file.replace('.hdr', '')
    meta_file = bin_file.replace('_raw', '_metadata.json')
    
    return bin_file, meta_file


# --------------------------------------------------
def get_scan_dir(meta_file):

    with open(meta_file) as f: 
        meta_dict = json.load(f)['lemnatec_measurement_metadata']
        scan_dir = meta_dict['gantry_system_variable_metadata']['scanDirectionIsPositive']
        
    return scan_dir, meta_dict


# --------------------------------------------------
def closest(lst, K):

    return min(enumerate(lst), key=lambda x: abs(x[1]-K))


# --------------------------------------------------
def rotate_img(img, scan_dir):
    
    if 'True' in scan_dir:
        img = np.rot90(img.asarray(), k=3)
        h, w, _ = img.shape
        

    elif 'False' in scan_dir:
        img = np.rot90(img.asarray(), k=1)
        img = np.flipud(img)
        h, w, _ = img.shape
        
        
    return img


# --------------------------------------------------
def generate_save_rgb(img, rot_img, out_name):

    args = get_args()
    wavelength_floats = [float(string) for string in img.metadata['wavelength']]
    
    r_band = closest(wavelength_floats, 669)[0]
    g_band = closest(wavelength_floats, 549)[0]
    b_band = closest(wavelength_floats, 474)[0]
    
    save_rgb(f'{os.path.join(args.rgb_outdir, out_name+".png")}', rot_img, bands=[r_band, g_band, b_band])


# --------------------------------------------------
def process_data(hdr_file):
    
    # Open necessary files 
    bin_file, meta_file = get_files(hdr_file)
    img = envi.open(hdr_file, bin_file)
    scan_dir, meta_dict = get_scan_dir(meta_file)

    # Rotate cube
    rot_img = rotate_img(img, scan_dir)
    out_name = bin_file.split('/')[-1].split('_')[0]

    # Generate pseudo-RGB image
    generate_save_rgb(img, rot_img, out_name)
    
    # Convert ENVI data to H5 with metadata
    with h5py.File(f'{os.path.join(args.h5_outdir, out_name+".h5")}', 'w') as data_file:

        data_file.create_dataset("hyperspectral", data=rot_img[:,:,:], chunks=True, compression='szip')
        
        dict_m = img.metadata

        for k,v in dict_m.items():
            data_file.attrs[k] = dict_m[k]
            
            
# --------------------------------------------------
def main():
    """Make a jazz noise here"""

    args = get_args()
    process_data(args.hdr_file)
    


# --------------------------------------------------
if __name__ == '__main__':
    main()
