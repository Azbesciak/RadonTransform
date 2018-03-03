from __future__ import print_function, division

import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, ifft

from skimage.io import imread
from skimage.transform import radon, rescale, rotate, iradon
from skimage.filters import gaussian

def draw_image(i, img):
    plt.subplot(1, 2, i)
    plt.imshow(img, cmap=plt.cm.Greys_r)


emitters_num = 40


def make_image_square(img):
    shape = img.shape
    if len(shape) != 2:
        raise Exception("Wrong shape " + str(shape))

    if shape[0] == shape[1]:
        return img

    max_shape = np.max(shape)
    result = pad_image(img, max_shape, shape)
    return result


def pad_image(img, required_size, shape):
    result = np.zeros((required_size, required_size))
    start_x = int((required_size - shape[0]) / 2)
    start_y = int((required_size - shape[1]) / 2)
    end_x = start_x + shape[0]
    end_y = start_y + shape[1]
    result[start_x:end_x, start_y:end_y] = img
    return result


def increase_image(img):
    shape = img.shape
    np_max_dim = np.max(shape)
    return pad_image(img, int(np_max_dim * np.sqrt(2)), shape)


def prepare_tomograph(emitters, dim):
    emitters = np.min((emitters, dim))
    zeros = np.zeros((dim, dim))
    distance = int(dim / emitters)
    start = int(np.ceil((dim % distance) / 2))
    zeros[:, start::distance] = 1
    zeros = gaussian(zeros)
    return zeros


def get_intersection(rotation, image, tomograph, real_dim):
    rotation += 90
    start = int((len(image) - real_dim) / 2)
    rotated = rotate(tomograph, rotation)
    common_part = rotated * image
    common_rotated_again = rotate(common_part, -rotation)
    column_avg = [sum(q) / real_dim for q in common_rotated_again[start:(start+real_dim)]]
    return column_avg


def inverse_radon(image, rotations):
    output_size = len(image)
    projection = fft(image, axis=0)
    radon_filtered = np.real(ifft(projection, axis=0))
    reconstructed = np.zeros((output_size, output_size))
    mid_index = image.shape[0] // 2

    [X, Y] = np.mgrid[0:output_size, 0:output_size]
    xpr = X - int(output_size) // 2
    ypr = Y - int(output_size) // 2
    th = (np.pi / 180.0) * rotations
    # Reconstruct image by interpolation
    for i in range(len(rotations)):
        theta = th[i]
        t = ypr * np.cos(theta) - xpr * np.sin(theta)
        x = np.arange(radon_filtered.shape[0]) - mid_index
        reconstructed += np.interp(t, x, radon_filtered[:, i],left=0, right=0)
    return reconstructed


image = imread("examples/CT_ScoutView.jpg", as_grey=True)
image = rescale(image, scale=0.4, mode='reflect')
image = make_image_square(image)
increased_image = increase_image(image)
tomograph = prepare_tomograph(emitters=emitters_num, dim=np.max(image.shape))
increased_tomograph = increase_image(tomograph)

res = []
theta = np.linspace(0., 180., max(image.shape), endpoint=False)
rotations = range(0, 360, 1)
for rotation in theta:
    res.append(get_intersection(rotation, increased_image, increased_tomograph, len(image)))
res = np.array(res)
fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(8, 8))

sinogram = radon(image, theta=theta, circle=True)

i_sin = inverse_radon(sinogram, theta)

ax1.imshow(image, cmap=plt.cm.Greys_r)
ax2.imshow(sinogram, cmap=plt.cm.Greys_r,
           extent=(0, 180, 0, sinogram.shape[0]), aspect='auto')
ax4.imshow(i_sin, cmap=plt.cm.Greys_r)
ax3.imshow(res, cmap=plt.cm.Greys_r)

fig.tight_layout()
plt.show()