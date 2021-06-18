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

    parser.add_argument('-h5',
                        '--h5_outdir',
                        help='H5 output directory',
                        metavar='h5_outdir',
                        type=str,
                        default='hsi_h5_out')

    parser.add_argument('-min',
                        '--min_x',
                        help='Minimum x value for cropping.',
                        metavar='min_x',
                        type=int,
                        default=0)   

    parser.add_argument('-max',
                        '--max_x',
                        help='Maximum x value for cropping. Defaults to the entire hyperspectral cube.',
                        metavar='max_x',
                        type=int,
                        required=False)  

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
def generate_ndvi_mask(rot_img, x_lim, wavelength_floats):
    
    # wavelength_floats = f.attrs['wavelength'].astype(float)
    # b1 = closest(wavelength_floats, 607.0)[0]
    # b2 = closest(wavelength_floats, 802.5)[0]
    b1 = closest(wavelength_floats, 640)[0]
    b2 = closest(wavelength_floats, 850)[0]

    mask = ndvi(rot_img[:, x_lim[0]:x_lim[1],:], b1, b2)
    mask = np.copy(mask)

    # mask[mask<0.4]=0
    # mask[mask>=0.4]=255
    mask[mask<0.3]=0
    mask[mask>=0.3]=255

    masked_array = rot_img[:, x_lim[0]:x_lim[1],:]
    masked_array = np.copy(masked_array)

    masked_array[np.where(mask==0)] = 0

    return mask, masked_array


# --------------------------------------------------
def get_mean_reflectance(masked_array):

    mean_refl_list = []
    mean_refl = np.zeros(masked_array.shape[2])

    for i in np.arange(masked_array.shape[2]):
        refl_band = masked_array[:,:,i]
        mean_refl[i] = np.ma.mean(refl_band[refl_band!=0])

    mean_refl_list.append(mean_refl)
    
    return mean_refl_list


# --------------------------------------------------
def process_data(hdr_file):
    
    args = get_args()
    
    # Open necessary files 
    bin_file, meta_file = get_files(hdr_file)
    img = envi.open(hdr_file, bin_file)
    wavelength_floats = [float(i) for i in img.metadata['wavelength']]
    scan_dir, meta_dict = get_scan_dir(meta_file)

    # Rotate cube
    rot_img = rotate_img(img, scan_dir)
    out_name = bin_file.split('/')[-1].split('_')[0]

    # Generate pseudo-RGB image
    generate_save_rgb(img, rot_img, out_name)

    # NDVI soil masking.
    if args.max_x is None:

        n_row, n_col, n_bands = rot_img.shape
        x_lim = (args.min_x, n_col)

    else: 
        x_lim = (args.min_x, args.max_x)

    ndvi_mask, ndvi_masked_array = generate_ndvi_mask(rot_img, x_lim, wavelength_floats)
    ndvi_mean_refl = get_mean_reflectance(ndvi_masked_array)

    # Convert ENVI data to H5 with metadata
    with h5py.File(f'{os.path.join(args.h5_outdir, out_name+".h5")}', 'w') as data_file:

        data_file.create_dataset('hyperspectral', data=rot_img[:,:,:], chunks=True, compression='szip')
        data_file.create_dataset('ndvi_mask', data=ndvi_mask)
        data_file.create_dataset('ndvi_mean_spectra', data=ndvi_mean_refl)
        
        dict_m = img.metadata

        for k,v in dict_m.items():
            data_file.attrs[k] = dict_m[k]

    print(f'Processing complete. See output at {args.h5_outdir}.')
            
            
# --------------------------------------------------
def main():
    """Make a jazz noise here"""

    args = get_args()

    if not os.path.isdir(args.rgb_outdir):
        os.makedirs(args.rgb_outdir)

    if not os.path.isdir(args.h5_outdir):
        os.makedirs(args.h5_outdir)

    process_data(args.hdr_file)
    

# --------------------------------------------------
if __name__ == '__main__':
    main()
