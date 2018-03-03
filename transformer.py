from __future__ import print_function, division

import numpy as np
import matplotlib.pyplot as plt

from skimage.io import imread
from skimage.transform import radon, rescale, rotate
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
    start = int((len(image) - real_dim) / 2)
    rotated = rotate(tomograph, rotation)
    common_part = rotated * image
    common_rotated_again = rotate(common_part, -rotation)
    column_avg = [sum(q) / real_dim for q in common_rotated_again[start:(start+real_dim)]]
    return column_avg


image = imread("examples/CT_ScoutView.jpg", as_grey=True)
image = rescale(image, scale=0.4, mode='reflect')
image = make_image_square(image)
increased_image = increase_image(image)
tomograph = prepare_tomograph(emitters=emitters_num, dim=np.max(image.shape))
increased_tomograph = increase_image(tomograph)

res = []
rotations = range(0, 720, 1)
for rotation in rotations:
    res.append(get_intersection(rotation/2, increased_image, increased_tomograph, len(image)))
res = np.array(res)
fig, (ax2, ax3) = plt.subplots(1, 2, figsize=(8, 8))
ax3.imshow(res, cmap=plt.cm.Greys_r)
# ax1.set_title("Original")
# ax1.imshow(image, cmap=plt.cm.Greys_r)
theta = np.linspace(0., 180., max(image.shape), endpoint=False)
sinogram = radon(image, theta=theta, circle=True)
ax2.set_title("Radon transform\n(Sinogram)")
ax2.set_xlabel("Projection angle (deg)")
ax2.set_ylabel("Projection position (pixels)")
ax2.imshow(sinogram, cmap=plt.cm.Greys_r,
           extent=(0, 180, 0, sinogram.shape[0]), aspect='auto')

fig.tight_layout()
plt.show()