#!/usr/bin/python
#! -*- encoding: utf-8 -*-


# Indicate the openMVG/MVS binary directory
OPENMVG_SFM_BIN = "/mnt/workspace/hobby/openMVG_Build/Linux-x86_64-RELEASE"
OPENMVS_BIN = "/mnt/workspace/hobby/openMVS_build/bin"

# Indicate the openMVG camera sensor width directory
CAMERA_SENSOR_WIDTH_DIRECTORY = "/mnt/workspace/hobby/openMVG/src/software/SfM" + "/../../openMVG/exif/sensor_width_database"

import os
import subprocess
import sys

def get_parent_dir(directory):
    return os.path.dirname(directory)

input_data_dir = sys.argv[1]
output_data_dir = sys.argv[2]

matches_dir = os.path.join(output_data_dir, "matches")
reconstruction_dir = os.path.join(output_data_dir, "reconstruction_sequential")
camera_file_params = os.path.join(CAMERA_SENSOR_WIDTH_DIRECTORY, "sensor_width_camera_database.txt")


print ("Using input data dir  : ", input_data_dir)
print ("      output data dir : ", output_data_dir)

matches_dir = os.path.join(output_data_dir, "matches")
camera_file_params = os.path.join(CAMERA_SENSOR_WIDTH_DIRECTORY, "sensor_width_camera_database.txt")

# Create the ouput/matches/reconstruction folder if not present
if not os.path.exists(output_data_dir):
  os.mkdir(output_data_dir)
if not os.path.exists(matches_dir):
  os.mkdir(matches_dir)
if not os.path.exists(reconstruction_dir):
    os.mkdir(reconstruction_dir)

print ("1. Intrinsics analysis")
pIntrisics = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_data_dir, "-o", matches_dir, "-d", camera_file_params, "-c", "3"] )
pIntrisics.wait()

print ("2. Compute features")
pFeatures = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeFeatures"),  "-i", matches_dir+"/sfm_data.json", "-o", matches_dir, "-m", "SIFT", "-f" , "1"] )
pFeatures.wait()

print ("3. Compute matches")
pMatches = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches"),  "-i", matches_dir+"/sfm_data.json", "-o", matches_dir, "-f", "1", "-n", "ANNL2"] )
pMatches.wait()

print ("4. Do Incremental/Sequential reconstruction") #set manually the initial pair to avoid the prompt question
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_IncrementalSfM"),  "-i", matches_dir+"/sfm_data.json", "-m", matches_dir, "-o", reconstruction_dir] )
pRecons.wait()

print ("5. Colorize Structure")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(reconstruction_dir,"colorized.ply")] )
pRecons.wait()

print ("6. Structure from Known Poses (robust triangulation)")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeStructureFromKnownPoses"),  "-i", reconstruction_dir+"/sfm_data.bin", "-m", matches_dir, "-o", os.path.join(reconstruction_dir,"robust.ply")] )
pRecons.wait()


# Reconstruction for the global SfM pipeline
# - global SfM pipeline use matches filtered by the essential matrices
# - here we reuse photometric matches and perform only the essential matrix filering
print ("+2. Compute matches (for the global SfM Pipeline)")
pMatches = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches"),  "-i", matches_dir+"/sfm_data.json", "-o", matches_dir, "-r", "0.8", "-g", "e"] )
pMatches.wait()

reconstruction_dir = os.path.join(output_data_dir,"reconstruction_global")
print ("+3. Do Global reconstruction")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_GlobalSfM"),  "-i", matches_dir+"/sfm_data.json", "-m", matches_dir, "-o", reconstruction_dir] )
pRecons.wait()

print ("+4. Colorize Structure")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(reconstruction_dir,"colorized.ply")] )
pRecons.wait()

print ("+5. Structure from Known Poses (robust triangulation)")
pRecons = subprocess.Popen( [os.path.join(OPENMVG_SFM_BIN, "openMVG_main_ComputeStructureFromKnownPoses"),  "-i", reconstruction_dir+"/sfm_data.bin", "-m", matches_dir, "-o", os.path.join(reconstruction_dir,"robust.ply")] )
pRecons.wait()

print ("+alpha. Extra process")
#pConvert = subprocess.Popen( [os.path.join(OPENMVS_BIN, "openMVG_main_openMVG2openMVS"),  "-i", reconstruction_dir+"/sfm_data.bin", "-o", os.path.join(reconstruction_dir,"scene.mvs")] )
#pConvert.wait()

pDensify = subprocess.Popen( [os.path.join(OPENMVS_BIN, "DensifyPointCloud"), os.path.join(reconstruction_dir,"scene.mvs")] )
pDensify.wait()

pMesh = subprocess.Popen( [os.path.join(OPENMVS_BIN, "ReconstructMesh"), os.path.join(reconstruction_dir,"scene_dense.mvs")] )
pMesh.wait()

pRefine = subprocess.Popen( [os.path.join(OPENMVS_BIN, "RefineMesh"), os.path.join(reconstruction_dir,"scene_mesh.mvs")] )
pRefine.wait()

pTexture = subprocess.Popen( [os.path.join(OPENMVS_BIN, "TextureMesh"), os.path.join(reconstruction_dir,"scene_dense_mesh.mvs")] )
pTexture.wait()
