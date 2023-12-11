import os

transfer_size = 75 # less than 100
for j in range(100-transfer_size, 100):
    os.rename('data/nerf_synthetic/bottles/rgb/1_val_{:04d}.png'.format(j), 'data/nerf_synthetic/bottles/rgb/0_train_{:04d}.png'.format(j+transfer_size))
    os.rename('data/nerf_synthetic/bottles/pose/1_val_{:04d}.txt'.format(j), 'data/nerf_synthetic/bottles/pose/0_train_{:04d}.txt'.format(j+transfer_size))

