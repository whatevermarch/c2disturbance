#!/usr/bin/env python3

import os
import numpy as np
import argparse
import sys
import subprocess
import random
from PIL import Image

DOWNLOADS_ROOT = 'ImageNet-Datasets-Downloader'
DOWNLOADER_PATH = os.path.join(DOWNLOADS_ROOT, 'downloader.py')
DOWNLOADS_PATH = os.path.join(DOWNLOADS_ROOT, 'imagenet_images')

BLENDER_ROOT = 'blender'
BLENDER_SAMPLE_NAME_FORMAT = "{:04d}.jpg"
BLENDER_SAMPLES_REL_PATH = 'samples'
BLENDER_OUTPUT_REL_PATH = 'output'
BLENDER_BLEND_REL_PATH = 'water_noise.blend'
BLENDER_SCRIPT_REL_PATH = os.path.join('scripts', 'main_render.py')
BLENDER_SAMPLES_PATH = os.path.join(BLENDER_ROOT, BLENDER_SAMPLES_REL_PATH)

def downloadClasses(downloader_path, n_classes, n_images_per_class, data_root):
    args_list = ['python', DOWNLOADER_PATH,
                '-number_of_classes', n_classes,
                '-images_per_class', n_images_per_class,
                '-data_root', data_root]
    args = ' '.join(str(arg) for arg in args_list)
    subprocess.call(args, shell=True)

def prepareBlenderData(input_dir, output_dir, n_samples, n_samples_per_class):
    os.makedirs(output_dir, exist_ok=True)
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

def generateDistortedImages(blender_root, rel_samples_dir,
        rel_output_dir, n_samples, n_frames_per_sample, wave_scale):
    args_list = ['blender',
                '-b', BLENDER_BLEND_REL_PATH,
                '-P', BLENDER_SCRIPT_REL_PATH,
                '--',
                '--sample_dir', rel_samples_dir,
                '--output_dir', rel_output_dir,
                '--samples', 0, n_samples - 1,
                '--frames', 1, n_frames_per_sample,
                '--wave_scale', wave_scale]
    args = ' '.join(str(arg) for arg in args_list)
    subprocess.call(args, shell=True, cwd=blender_root)

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
    parser.add_argument('--wave_scale', default = 0.0, type=float)
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

    downloadClasses(
            DOWNLOADER_PATH,
            args.number_of_classes,
            args.images_per_class,
            DOWNLOADS_ROOT)
    prepareBlenderData(
            DOWNLOADS_PATH,
            BLENDER_SAMPLES_PATH,
            args.total_images,
            args.images_per_class)
    generateDistortedImages(
            BLENDER_ROOT,
            BLENDER_SAMPLES_REL_PATH,
            BLENDER_OUTPUT_REL_PATH,
            args.total_images,
            args.frames_per_image,
            args.wave_scale)

    cleanUp([DOWNLOADS_PATH, BLENDER_SAMPLES_PATH])
