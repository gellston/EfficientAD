import numpy as np
from torch.utils.data import Dataset, DataLoader
import torch
import cv2
import glob
import csv
import logging
import shutil
import imgaug.augmenters as iaa
# from perlin import rand_perlin_2d_np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms
import pdb
import os
from PIL import Image

class MVTecDataset(Dataset):
    def __init__(self, root, transform, gt_transform, phase):
        if phase=='train':
            self.img_path = os.path.join(root, 'train')
        else:
            self.img_path = os.path.join(root, 'test')
            self.gt_path = os.path.join(root, 'ground_truth')
        self.transform = transform
        self.gt_transform = gt_transform
        # load dataset
        self.img_paths, self.gt_paths, self.labels, self.types = self.load_dataset() # self.labels => good : 0, anomaly : 1

    def load_dataset(self):
        img_tot_paths = []
        gt_tot_paths = []
        tot_labels = []
        tot_types = []

        defect_types = os.listdir(self.img_path)
        
        for defect_type in defect_types:
            if defect_type == 'good':
                img_paths = glob.glob(os.path.join(self.img_path, defect_type) + "/*.png")
                img_tot_paths.extend(img_paths)
                gt_tot_paths.extend([0]*len(img_paths))
                tot_labels.extend([0]*len(img_paths))
                tot_types.extend(['good']*len(img_paths))
            else:
                img_paths = glob.glob(os.path.join(self.img_path, defect_type) + "/*.png")
                gt_paths = glob.glob(os.path.join(self.gt_path, defect_type) + "/*.png")
                img_paths.sort()
                gt_paths.sort()
                img_tot_paths.extend(img_paths)
                if len(gt_paths)==0:
                    gt_paths = [0]*len(img_paths)
                
                gt_tot_paths.extend(gt_paths)
                tot_labels.extend([1]*len(img_paths))
                tot_types.extend([defect_type]*len(img_paths))

        assert len(img_tot_paths) == len(gt_tot_paths), "Something wrong with test and ground truth pair!"

        return img_tot_paths, gt_tot_paths, tot_labels, tot_types

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img_path, gt, label, img_type = self.img_paths[idx], self.gt_paths[idx], self.labels[idx], self.types[idx]
        img = Image.open(img_path).convert('RGB')
        img = self.transform(img)
        if gt == 0:
            gt = torch.zeros([1, img.size()[-2], img.size()[-2]])
        else:
            gt = Image.open(gt)
            gt = self.gt_transform(gt)
        
        assert img.size()[1:] == gt.size()[1:], "image.size != gt.size !!!"

        # return img, gt, label, os.path.basename(img_path[:-4]), img_type
        return {
            'image': img,
            'gt': gt,
            'label': label,
            'name': os.path.basename(img_path[:-4]),
            'type': img_type
        }
    
class MVTecLOCODataset(Dataset):

    def __init__(self, root, transform, gt_transform, phase):
        if phase=='train':
            self.img_path = os.path.join(root, 'train')
        else:
            self.img_path = os.path.join(root, 'test')
            self.gt_path = os.path.join(root, 'ground_truth')
        self.transform = transform
        self.gt_transform = gt_transform
        # load dataset
        self.img_paths, self.gt_paths, self.labels, self.types = self.load_dataset() # self.labels => good : 0, anomaly : 1


    def load_dataset(self):

        img_tot_paths = []
        gt_tot_paths = []
        tot_labels = []
        tot_types = []

        defect_types = os.listdir(self.img_path)
        
        for defect_type in defect_types:
            if defect_type == 'good':
                img_paths = glob.glob(os.path.join(self.img_path, defect_type) + "/*.png")
                img_tot_paths.extend(img_paths)
                gt_tot_paths.extend([0]*len(img_paths))
                tot_labels.extend([0]*len(img_paths))
                tot_types.extend(['good']*len(img_paths))
            else:
                img_paths = glob.glob(os.path.join(self.img_path, defect_type) + "/*.png")
                gt_paths = glob.glob(os.path.join(self.gt_path, defect_type) + "/*")
                gt_paths = [g for g in gt_paths if os.path.isdir(g)]
                img_paths.sort()
                gt_paths.sort()
                img_tot_paths.extend(img_paths)
                if len(gt_paths)==0:
                    gt_paths = [0]*len(img_paths)
                
                gt_tot_paths.extend(gt_paths)
                tot_labels.extend([1]*len(img_paths))
                tot_types.extend([defect_type]*len(img_paths))

        assert len(img_tot_paths) == len(gt_tot_paths), "Something wrong with test and ground truth pair!"

        return img_tot_paths, gt_tot_paths, tot_labels, tot_types


    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img_path, gt, label, img_type = self.img_paths[idx], self.gt_paths[idx], self.labels[idx], self.types[idx]
        img = Image.open(img_path).convert('RGB')
        img = self.transform(img)
        if gt == 0:
            gt = torch.zeros([1, img.size()[-2], img.size()[-2]])
        else:
            names = os.listdir(gt)
            ims = [cv2.imread(os.path.join(gt, name), cv2.IMREAD_GRAYSCALE) for name in names]
            ims = [im for im in ims if isinstance(im, np.ndarray)]
            imzeros = np.zeros_like(ims[0])
            for im in ims:
                imzeros[im==255] = 255
            gt = Image.fromarray(imzeros)
            gt = self.gt_transform(gt)
        
        assert img.size()[1:] == gt.size()[1:], "image.size != gt.size !!!"

        # return img, gt, label, os.path.basename(img_path[:-4]), img_type
        return {
            'image': img,
            'gt': gt,
            'label': label,
            'name': os.path.basename(img_path[:-4]),
            'type': img_type
        }
    
class VisaDataset(Dataset):

    def __init__(self, root, transform, gt_transform, phase, category=None):
        self.phase = phase
        self.root = root
        self.category = category
        self.transform = transform
        self.gt_transform = gt_transform
        self.split_file = self.root + "../split_csv" + "/1cls.csv"
        self.img_paths, self.gt_paths, self.labels, self.types = self.load_dataset() # self.labels => good : 0, anomaly : 1


    def load_dataset(self):

        img_tot_paths = []
        gt_tot_paths = []
        tot_labels = []
        tot_types = []
        with self.split_file.open(encoding="utf-8") as file:
            csvreader = csv.reader(file)
            next(csvreader)
            for row in csvreader:
                category, split, label, image_path, mask_path = row
                if label == "normal":
                    label = "good"
                else:
                    label = "bad"
                image_name = image_path.split("/")[-1]
                mask_name = mask_path.split("/")[-1]
                if self.phase == "train" and self.category == category:
                    img_src_path = os.path.join(self.root,image_path)
                    if label == "normal":
                        gt_src_path = 0
                        index = 0
                        types = "good"
                    else:
                        index = 1
                        types = "bad"
                        gt_src_path = os.path.join(self.root,mask_path)
                    img_tot_paths.append(img_src_path)
                    gt_tot_paths.append(gt_src_path)
                    tot_labels.append(index)
                    tot_types.append(types)
        return img_tot_paths, gt_tot_paths, tot_labels, tot_types

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img_path, gt, label, img_type = self.img_paths[idx], self.gt_paths[idx], self.labels[idx], self.types[idx]
        img = Image.open(img_path).convert('RGB')
        img = self.transform(img)
        if gt == 0:
            gt = torch.zeros([1, img.size()[-2], img.size()[-2]])
        else:
            gt = Image.open(gt)
            gt = self.gt_transform(gt)
        
        assert img.size()[1:] == gt.size()[1:], "image.size != gt.size !!!"

        # return img, gt, label, os.path.basename(img_path[:-4]), img_type
        return {
            'image': img,
            'gt': gt,
            'label': label,
            'name': os.path.basename(img_path[:-4]),
            'type': img_type
        }



class ImageNetDataset(Dataset):
    def __init__(self, imagenet_dir,transform=None,):
        super().__init__()
        self.imagenet_dir = imagenet_dir
        self.transform = transform
        self.dataset = ImageFolder(self.imagenet_dir, transform=self.transform)

    def __len__(self):
        return 10000

    def __getitem__(self, idx):
        return self.dataset[idx][0]
    
def load_infinite(loader):
    iterator = iter(loader)
    while True:
        try:
            yield next(iterator)
        except StopIteration:
            iterator = iter(loader)


            
def get_AD_Dataset(type, root, transform, gt_transform, phase, category=None):
    if type == "Visa":
        return VisaDataset(root, transform, gt_transform, phase, category)
    elif type == "MVTec":
        return MVTecDataset(root, transform, gt_transform, phase, category)
    elif type == 'MVTecLoco':
        return MVTecLOCODataset(root, transform, gt_transform, phase, category)
    elif type == 'ImageNet':
        return ImageNetDataset(root, transform)
    else:
        raise NotImplementedError