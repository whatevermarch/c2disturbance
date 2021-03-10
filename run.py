#!/usr/bin/env python3

import os
import numpy as np
import argparse
import sys
import subprocess
import random
from PIL import Image
import json

DOWNLOADS_ROOT = 'ImageNet-Datasets-Downloader'
DOWNLOADER_PATH = os.path.join(DOWNLOADS_ROOT, 'downloader.py')
DOWNLOADS_PATH = os.path.join(DOWNLOADS_ROOT, 'imagenet_images')

BLENDER_ROOT = 'blender'
BLENDER_SAMPLE_NAME_FORMAT = "{:04d}.jpg"
BLENDER_SAMPLE_PARAM_FILE_NAME = "distortion_params.json"
BLENDER_SAMPLES_REL_PATH = 'samples'
BLENDER_OUTPUT_REL_PATH = 'output'
BLENDER_BLEND_REL_PATH = 'water_noise.blend'
BLENDER_SCRIPT_REL_PATH = os.path.join('scripts', 'main_render.py')
BLENDER_SAMPLES_PATH = os.path.join(BLENDER_ROOT, BLENDER_SAMPLES_REL_PATH)

def downloadClasses(downloader_path, n_classes, n_images_per_class, data_root):
    args_list = ['python', DOWNLOADER_PATH,
                '-number_of_classes', n_classes,
                '-images_per_class', n_images_per_class + 5,
                '-data_root', data_root]
    args = ' '.join(str(arg) for arg in args_list)
    subprocess.call(args, shell=True)

def prepareBlenderData(input_dir, output_dir, n_samples, n_samples_per_class, wave_scale, amplifier):
    os.makedirs(output_dir, exist_ok=True)

    #   prepare parameters dictionary
    params = {}
    params['wave_scales'] = [] if wave_scale == 0.0 else [wave_scale] * n_samples
    params['amplifiers'] = [] if amplifier == 0.0 else [amplifier] * n_samples

    sm = 0

    next_sample_id = 0
    for cls in os.listdir(input_dir):
        cls_path = os.path.join(input_dir, cls)
        samples = os.listdir(cls_path)
        random.shuffle(samples)
        samples = samples[:n_samples_per_class]

        for sample_name in samples:
            if next_sample_id == n_samples:
                break
            sample_path = os.path.join(cls_path, sample_name)
            new_sample_name = BLENDER_SAMPLE_NAME_FORMAT.format(next_sample_id)
            new_sample_path = os.path.join(output_dir, new_sample_name)
            image = Image.open(sample_path)
            image.save(new_sample_path)
            next_sample_id += 1

            #   generate this sample's distortion parameter
            if wave_scale == 0.0:
                params['wave_scales'].append( random.uniform( 5.0, 6.5 ) )
            if amplifier == 0.0:
                params['amplifiers'].append( random.uniform( 0.4, 0.5 ) )
        sm += len(samples)
        #if (len(samples) < 10):
        #    print(cls, len(samples))
        #print(cls, len(samples))

    print("XX: ", sm)
    #print("YY: ", params["wave_scales"], len(params["amplifiers"]))

    #   save parameters as JSON file
    with open( os.path.join( BLENDER_ROOT, BLENDER_SAMPLE_PARAM_FILE_NAME ), "w" ) as param_fp:
        json.dump( params, param_fp )

def generateDistortedImages(blender_root, rel_samples_dir,
        rel_output_dir, n_samples, n_frames_per_sample, used_gpus):

    args_list = [
                #'blender',
                '/opt/blender-2.83.7-linux64/blender',
                '-b', BLENDER_BLEND_REL_PATH,
                '-P', BLENDER_SCRIPT_REL_PATH,
                '--',
                '--sample_dir', rel_samples_dir,
                '--output_dir', rel_output_dir,
                '--samples', 0, n_samples - 1,
                '--frames', 1, n_frames_per_sample,
                '--param_file', BLENDER_SAMPLE_PARAM_FILE_NAME]
    
    #   if no GPU specified, use all
    if not used_gpus:
        args = ' '.join(str(arg) for arg in args_list)
        subprocess.call(args, shell=True, cwd=blender_root)
    else:
        #   determine the amount of samples on which each GPU will work
        num_gpus = len(used_gpus)
        n_samples_per_gpu = [ n_samples // num_gpus ] * num_gpus
        rem_n_samples = n_samples % num_gpus
        for i in range( num_gpus ):
            if rem_n_samples == 0:
                break
            n_samples_per_gpu[i] += 1
            rem_n_samples -= 1

        #   launch separated processes for each GPU defined
        logs = []
        procs = []
        args_list.extend( [ '--gpu_id', -1 ] )
        args_list[12] = n_samples_per_gpu[-1] - 1
        for i in range( num_gpus ):
            args_list[-1] = used_gpus[i]
            args = ' '.join(str(arg) for arg in args_list)

            logs.append( open( os.path.join( BLENDER_ROOT, BLENDER_OUTPUT_REL_PATH, "render.log." + str(i + 1) ) , "w" ) )

            procs.append( subprocess.Popen(args, shell=True, cwd=blender_root, stdout=logs[-1], stderr=sys.stderr) )

            args_list[11] = args_list[12] + 1
            args_list[12] = args_list[11] + n_samples_per_gpu.pop() - 1

            print(n_samples_per_gpu[i], args_list)

        #   synchronize all processes and close logging file descriptors
        for i in range( num_gpus ):
            procs[i].wait()
            logs[i].close()

def cleanUp(dirs):
    for d in dirs:
        if os.name == 'nt':
            subprocess.call('rmdir /s /q {}'.format(d), shell=True)
        else:
            subprocess.call('rm -r {}'.format(d), shell=True)
    print('Cleaned up')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--number_of_classes', default = -1, type=int)
    parser.add_argument('--images_per_class', default = 1, type=int)
    parser.add_argument('--total_images', default = -1, type=int)
    parser.add_argument('--frames_per_image', default = 30, type=int)
    parser.add_argument('--wave_scale', default = 0.0, type=float, 
        help='''scale of wave that distort the view. recommended values are between 3.2 - 8.0. 
                    this will be applied to **ALL** samples. if you are not certain, 
                    leave this parameter to let the script properly randomize for **EACH** sample.''' )
    parser.add_argument('--amplifier', default = 0.0, type=float,
        help='''distortion amplifier. recommended values are between 0.17 - 0.56. 
                    this will be applied to **ALL** samples. if you are not certain, 
                    leave this parameter to let the script properly randomize for **EACH** sample.''' )
    parser.add_argument('--gpus', default = [], type=int, nargs='+', 
        help='''identify gpu index (CUDA) used to render the distortion (ex. --gpus 0 1 2). 
                    use \'nvidia-smi\' to list all available gpu indices in the current system.''')
    args = parser.parse_known_args()[0]

    if args.total_images <= 0 and args.number_of_classes <= 0:
        print("either --total_images or --number_of_classes must be specified")
        exit()

    # if args.total_images <= 0:
    #     args.total_images = args.number_of_classes * args.images_per_class
    # elif args.number_of_classes == -1:
    
    # prefer the number of classes over total images
    if args.number_of_classes <= 0:
        args.number_of_classes = ( args.total_images + args.images_per_class - 1 ) // args.images_per_class
    else:
        args.total_images = args.number_of_classes * args.images_per_class

    for gpu in args.gpus:
        if gpu < 0:
            print("--gpus specified invalid GPU index")
            exit()

    #downloadClasses(
    #        DOWNLOADER_PATH,
    #        args.number_of_classes,
    #        args.images_per_class,
    #        DOWNLOADS_ROOT)
    prepareBlenderData(
            DOWNLOADS_PATH,
            BLENDER_SAMPLES_PATH,
            args.total_images,
            args.images_per_class,
            args.wave_scale,
            args.amplifier)
    generateDistortedImages(
            BLENDER_ROOT,
            BLENDER_SAMPLES_REL_PATH,
            BLENDER_OUTPUT_REL_PATH,
            args.total_images,
            args.frames_per_image,
            args.gpus)

    #cleanUp([DOWNLOADS_PATH, BLENDER_SAMPLES_PATH])
