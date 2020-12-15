#!/usr/bin/env python3

import os
import random
import shutil

INPUT_PATH = os.path.join("blender", "output")
DATA_PATH = "data"
TEST_PATH = os.path.join(DATA_PATH, "Water_Real", "test")
TRAIN_PATH = os.path.join(DATA_PATH, "Water", "train")
VAL_PATH = os.path.join(DATA_PATH, "Water", "test")

ORIG_TRAIN_PATH = os.path.join(DATA_PATH, "ImageNet", "train")
ORIG_VAL_PATH = os.path.join(DATA_PATH, "ImageNet", "test")

VAL_PERCENT = 0.15
TEST_PERCENT = 0.15

def getAllImages(input_path):
    imgs = []
    input_path = os.path.join(input_path, 'distorted')
    for sample in os.listdir(input_path):
        sample_path = os.path.join(input_path, sample)
        for frame in os.listdir(sample_path):
            imgs.append((sample, frame))
    return imgs

def prepareTrainData(input_path, imgs, dist_path, orig_path):
    os.makedirs(dist_path, exist_ok=True)
    os.makedirs(orig_path, exist_ok=True)
    for sample, frame in imgs:
        old_dist = os.path.join(
                input_path, 'distorted',
                sample, frame)
        new_dist = os.path.join(dist_path, sample + '_' + frame)
        old_orig = os.path.join(
                input_path, 'undistorted',
                sample + '.' + frame.split('.')[-1])
        new_orig = os.path.join(orig_path, sample + '_' + frame)
        shutil.copy(old_dist, new_dist)
        shutil.copy(old_orig, new_orig)

def prepareTestData(input_path, imgs, output_path):
    input_path = os.path.join(input_path, 'distorted')
    os.makedirs(output_path, exist_ok=True)
    for sample, frame in imgs:
        old_path = os.path.join(input_path, sample, frame)
        new_path = os.path.join(output_path, sample + '_' + frame)
        shutil.copy(old_path, new_path)

if __name__ == "__main__":
    imgs = getAllImages(INPUT_PATH)
    random.shuffle(imgs)

    val_img_idx = 0
    n_val_imgs = int(len(imgs) * VAL_PERCENT)
    val_imgs = imgs[val_img_idx: val_img_idx + n_val_imgs]

    test_img_idx = n_val_imgs
    n_test_imgs = int(len(imgs) * TEST_PERCENT)
    test_imgs = imgs[test_img_idx: test_img_idx + n_test_imgs]

    train_img_idx = n_val_imgs + n_test_imgs
    n_train_imgs = len(imgs) - (n_test_imgs + n_val_imgs)
    train_imgs = imgs[train_img_idx: train_img_idx + n_train_imgs]

    prepareTrainData(INPUT_PATH, train_imgs, TRAIN_PATH, ORIG_TRAIN_PATH)
    prepareTrainData(INPUT_PATH, val_imgs, VAL_PATH, ORIG_VAL_PATH)
    prepareTestData(INPUT_PATH, test_imgs, TEST_PATH)
