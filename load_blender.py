import os
import torch
import numpy as np
# import imageio
import imageio.v3 as iio 
import json
import torch.nn.functional as F
import cv2


trans_t = lambda t : torch.Tensor([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,1,t],
    [0,0,0,1]]).float()

rot_phi = lambda phi : torch.Tensor([
    [1,0,0,0],
    [0,np.cos(phi),-np.sin(phi),0],
    [0,np.sin(phi), np.cos(phi),0],
    [0,0,0,1]]).float()

rot_theta = lambda th : torch.Tensor([
    [np.cos(th),0,-np.sin(th),0],
    [0,1,0,0],
    [np.sin(th),0, np.cos(th),0],
    [0,0,0,1]]).float()


def pose_spherical(theta, phi, radius):
    c2w = trans_t(radius)
    c2w = rot_phi(phi/180.*np.pi) @ c2w
    c2w = rot_theta(theta/180.*np.pi) @ c2w
    c2w = torch.Tensor(np.array([[-1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])) @ c2w
    return c2w


def load_blender_data_bottles(basedir, half_res=False, testskip=1):
    # TODO: only train and val are ok to run
    splits = ['train', 'val', 'test']
    split_sizes = [175, 25, 200]

    all_imgs = []
    all_poses = []
    counts = [0]
    pose_index = 0

    # load rgb images and poses 
    for i in range(len(splits)):
        stype = splits[i]
        ssize = split_sizes[i]
        imgs = []
        poses = []
        if stype=='train' or testskip==0:
            skip = 1
        else:
            skip = testskip
            
        is_test = False
        if i==2: # at test state, no rgb is provided
            is_test = True
        for j in range(ssize):
            if not is_test:
                imgfname = os.path.join(basedir, "rgb", "{}_{}_{:04d}.png".format(i, stype, j))
                img = iio.imread(imgfname)
                # print(img.shape)
                imgs.append(img)
            posefname = os.path.join(basedir, "pose", "{}_{}_{:04d}.txt".format(i, stype, j))
            pose = np.array(np.loadtxt(posefname))
            pose[:, 1:3] *= -1
            poses.append(pose)

        poses = np.array(poses).astype(np.float32)
        counts.append(counts[-1] + ssize) # pose index count
        all_poses.append(poses)
        pose_index += 1
        if not is_test:
            imgs = (np.array(imgs) / 255.).astype(np.float32) # keep all 4 channels (RGBA)
            all_imgs.append(imgs)

    i_split = [np.arange(counts[i], counts[i+1]) for i in range(3)]
    
    imgs = np.concatenate(all_imgs, 0)
    poses = np.concatenate(all_poses, 0)
    
    # load intrinsics
    K = np.loadtxt(os.path.join(basedir, "intrinsics.txt"))
    H, W, focal = int(K[0, 2]*2), int(K[1, 2]*2), K[0, 0]
    
    # init random 40 poses for in-training testing
    # TODO: load some test poses as  render_poses
    render_poses = torch.stack([pose_spherical(angle, -30.0, 4.0) for angle in np.linspace(-180,180,40+1)[:-1]], 0)
    
    print(imgs.shape)
    if half_res:
        H = H//4
        W = W//4
        focal = focal/4.

        imgs_half_res = np.zeros((imgs.shape[0], H, W, 4))
        for i, img in enumerate(imgs):
            imgs_half_res[i] = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
        imgs = imgs_half_res
        # imgs = tf.image.resize_area(imgs, [400, 400]).numpy()

    return imgs, poses, render_poses, [H, W, focal], i_split



def load_blender_data(basedir, half_res=False, testskip=1):
    # TODO: only train and val are ok to run
    splits = ['train', 'val', 'test']
    metas = {}
    for s in splits:
        with open(os.path.join(basedir, 'transforms_{}.json'.format(s)), 'r') as fp:
            metas[s] = json.load(fp)

    all_imgs = []
    all_poses = []
    counts = [0]
    for s in splits:
        meta = metas[s]
        imgs = []
        poses = []
        if s=='train' or testskip==0:
            skip = 1
        else:
            skip = testskip
            
        for frame in meta['frames'][::skip]:
            fname = os.path.join(basedir, frame['file_path'] + '.png')
            imgs.append(iio.imread(fname))
            poses.append(np.array(frame['transform_matrix']))
        imgs = (np.array(imgs) / 255.).astype(np.float32) # keep all 4 channels (RGBA)
        poses = np.array(poses).astype(np.float32)
        counts.append(counts[-1] + imgs.shape[0])
        all_imgs.append(imgs)
        all_poses.append(poses)

    i_split = [np.arange(counts[i], counts[i+1]) for i in range(3)]
    
    imgs = np.concatenate(all_imgs, 0)
    poses = np.concatenate(all_poses, 0)
    
    # TODO: camera_angle_x or intrinsic-based focal length determination implementations
    H, W = imgs[0].shape[:2]
    camera_angle_x = float(meta['camera_angle_x'])
    focal = .5 * W / np.tan(.5 * camera_angle_x)
    
    # init random 40 poses for in-training testing
    render_poses = torch.stack([pose_spherical(angle, -30.0, 4.0) for angle in np.linspace(-180,180,40+1)[:-1]], 0)
    
    if half_res:
        H = H//2
        W = W//2
        focal = focal/2.

        imgs_half_res = np.zeros((imgs.shape[0], H, W, 4))
        for i, img in enumerate(imgs):
            imgs_half_res[i] = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
        imgs = imgs_half_res
        # imgs = tf.image.resize_area(imgs, [400, 400]).numpy()

        
    return imgs, poses, render_poses, [H, W, focal], i_split

