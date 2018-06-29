"""
Train SegNet based Siamese network

usage: train.py --dataset_root /home/SharedData/intern_sayan/iCoseg/ \
                --img_dir images \
                --mask_dir ground_truth \
                --checkpoint_load_dir /home/SharedData/intern_sayan/iCoseg/ \
                --gpu 1
"""

import argparse
from dataset import iCosegDataset
from model import SiameseSegNet
import os
import pdb
from tensorboardX import SummaryWriter
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

#-----------#
# Arguments #
#-----------#

parser = argparse.ArgumentParser(description='Train a SegNet model')

parser.add_argument('--dataset_root', required=True)
parser.add_argument('--img_dir', required=True)
parser.add_argument('--mask_dir', required=True)
parser.add_argument('--checkpoint_load_dir', default=False)
parser.add_argument('--gpu', default=None)

args = parser.parse_args()

#-----------#
# Constants #
#-----------#

## Debug

DEBUG = False

## Optimiser
LEARNING_RATE = 0.0001
BETAS = (0.9, 0.999)

## Dataset
BATCH_SIZE = 2 * 1 # two images at a time for Siamese net
INPUT_CHANNELS = 3 # RGB
OUTPUT_CHANNELS = 2 # BG + FG channel

## Training
CUDA = args.gpu
CHECKPOINT = args.checkpoint_save_dir
LOAD_CHECKPOINT = args.checkpoint_load_dir
NUM_EPOCHS = 1000



def infer():
    model.eval()

    t_start = time.time()

    for batch_idx, batch in tqdm(enumerate(dataloader)):
        images = batch["image"].type(FloatTensor)
        labels = batch["label"].type(LongTensor)
        masks  = batch["mask"].type(FloatTensor)

        # pdb.set_trace()

        pairwise_images = [(images[2*idx], images[2*idx+1]) for idx in range(BATCH_SIZE//2)]
        pairwise_labels = [(labels[2*idx], labels[2*idx+1]) for idx in range(BATCH_SIZE//2)]
        pairwise_masks  = [(masks[2*idx], masks[2*idx+1]) for idx in range(BATCH_SIZE//2)]

        # pdb.set_trace()

        imagesA, imagesB = zip(*pairwise_images)
        labelsA, labelsB = zip(*pairwise_labels)
        masksA, masksB = zip(*pairwise_masks)

        imagesA, imagesB = torch.stack(imagesA), torch.stack(imagesB)
        labelsA, labelsB = torch.stack(labelsA), torch.stack(labelsB)
        masksA, masksB = torch.stack(masksA).long(), torch.stack(masksB).long()

        # pdb.set_trace()

        imagesA_v = torch.autograd.Variable(FloatTensor(imagesA))
        imagesB_v = torch.autograd.Variable(FloatTensor(imagesB))

        pmapA, pmapB = model(imagesA_v, imagesB_v)

    delta = time.time() - t_start


if __name__ == "__main__":
    root_dir = args.dataset_root

    image_dir = os.path.join(root_dir, args.img_dir)
    mask_dir = os.path.join(root_dir, args.mask_dir)

    iCoseg_dataset = iCosegDataset(image_dir=image_dir,
                                   mask_dir=mask_dir)

    dataloader = DataLoader(iCoseg_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, drop_last=True)

    #-------------#
    #    Model    #
    #-------------#

    model = SiameseSegNet(input_channels=INPUT_CHANNELS,
                          output_channels=OUTPUT_CHANNELS,
                          gpu=CUDA)

    if DEBUG:
        print(model)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, betas=BETAS)

    FloatTensor = torch.FloatTensor
    LongTensor = torch.LongTensor

    if CUDA is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

        model = model.cuda()
        criterion = criterion.cuda()

        FloatTensor = torch.cuda.FloatTensor
        LongTensor = torch.cuda.LongTensor

    if LOAD_CHECKPOINT:
        model.load_state_dict(torch.load(LOAD_CHECKPOINT))


    #------------#
    #    Test    #
    #------------#

    infer()