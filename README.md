# hsi_envi_to_h5

# Hyperspectral Image ENVI to H5
This is a repository that includes all the code to convert an ENVI format hyperspectral image into H5 format. The docker file can be used to create a container image (or a singularity image) and use it to run (exec) the envi_to_h5.py script. The output of this repository is the H5 file. 

## Input Arguments

* Required Arguments:
    * The path to the hdr file: path
    * Path to the RGB output directory: rgb_outdir (-r --rgb_outdir)
    * The path to the H5 file output directory: h5_outdir (-h5 --h5_outdir)

* Optional Arguments:
    * The minimum x value for cropping: min_x (-min --min_x), default = 0
    * The maximum x value for cropping: max_x (-max --max_x), default = entire hyperspectral cube

## Running the Script

* Docker:
    * Docker run docker://phytooracle/hsi_envi_to_h5 [params]
* Singularity:
    * Singularity run docker://phytooracle/hsi_envi_to_h5 [params]
