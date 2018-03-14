from __future__ import print_function, division

import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fftfreq, fft, ifft
from skimage.filters import gaussian
from skimage.io import imread
from skimage.transform import rescale, rotate
import warnings


img_name_root = "examples/"
images = [
    "CT_ScoutView.jpg",
    "CT_ScoutView-large.jpg",
    "Kolo.jpg",
    "Kropka.jpg",
    "Kwadraty2.jpg",
    "Paski2.jpg",
    "SADDLE_PE.JPG",
    "SADDLE_PE-large.JPG",
    "Shepp_logan.jpg"
]
images = [img_name_root + n for n in images]

image_indx = 4

class Parameters:
    def __init__(self, alpha, emitters_num, use_filter, image_name) -> None:
        self.alpha = alpha
        self.emitters_num = emitters_num
        self.use_filter = use_filter
        self.image_name = image_name

    def set_values(self, alpha, emitters_num, use_filter, image_name):
        if alpha <= 0:
            raise Exception("Alpha must be positive")
        if emitters_num <=0:
            raise Exception("Emitters num must be positive")
        if image_name is None:
            raise Exception("Image was not selected")
        self.alpha = alpha
        self.emitters_num = emitters_num
        self.use_filter = use_filter
        self.image_name = image_name


params = Parameters(360/1440, 40, True, images[image_indx])


def draw_image(i, img):
    plt.subplot(1, 2, i)
    plt.imshow(img, cmap=plt.cm.Greys_r)


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


def create_filter_at(target, start, distance, filter):
    half_len = len(filter) // 2
    for i in range(len(filter)):
        to_write = i - half_len,
        target[:, start+to_write[0]::distance] = filter[i]


def prepare_tomograph(emitters, dim):
    if emitters > dim:
        warnings.warn("emmiters num was bigger than image dim - used smaller")
    emitters = np.min((emitters, dim))
    zeros = np.zeros((dim, dim))
    distance = int(dim / emitters)
    start = int(np.ceil((dim % distance) / 2))
    create_filter_at(zeros, start, distance, [1])
    zeros = gaussian(zeros)
    zeros /= zeros.max()
    return zeros


def get_intersection(rotation, image, tomograph, real_dim):
    rotation += 90
    target_size = len(image)
    start = int((target_size - real_dim) / 2)
    rotated = rotate(tomograph, rotation)
    common_part = rotated * image
    common_rotated_again = rotate(common_part, -rotation)
    column_avg = [sum(q)/real_dim for q in common_rotated_again[start:(start+real_dim)]]
    return column_avg


def make_radon(increased_image, increased_tomograph, real_dim, theta):
    res = np.zeros((len(theta), real_dim))
    for i, rotation in enumerate(theta):
        res[i] = get_intersection(rotation, increased_image, increased_tomograph, real_dim)
    return res


def transform_sinogram(sinogram):
    sinogram = np.rot90(sinogram, k=1)
    freqs = sinogram.shape[0]
    projection_size_padded = \
        max(64, int(2 ** np.ceil(np.log2(2 * freqs))))
    pad_width = ((0, projection_size_padded - freqs), (0, 0))
    img = np.pad(sinogram, pad_width, mode='constant', constant_values=0)
    f = fftfreq(projection_size_padded).reshape(-1, 1)
    omega = 2 * np.pi * f
    fourier_filter = 2 * np.abs(f)# * np.cos(omega)
    projection = fft(img, axis=0) * fourier_filter
    radon_filtered = np.real(ifft(projection, axis=0))
    radon_filtered = radon_filtered[:freqs, :]
    return np.rot90(radon_filtered, k=-1)


def inverse_radon(sigmoid, rotations, output_size):
    reconstructed = increase_image(np.zeros((output_size, output_size)))
    start = (len(reconstructed) - output_size)//2
    end = start + output_size
    rotations_len = len(rotations)
    for i in range(rotations_len):
        temp = np.array([sigmoid[i], ] * len(reconstructed))
        temp = make_image_square(temp)
        reconstructed += rotate(temp, rotations[i])
    result = reconstructed[start:end, start:end]
    if rotations_len > 0:
        result /= rotations_len
    return result


def get_moves(a):
    return [a * i for i in range(int(np.ceil(360 / a)))]


def show_images(original, sinogram, reconstructed):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(8, 8))
    ax1.imshow(original, cmap=plt.cm.Greys_r)
    ax2.imshow(sinogram, cmap=plt.cm.Greys_r)
    ax3.imshow(reconstructed, cmap=plt.cm.Greys_r)

    fig.tight_layout()
    plt.show()


def transform_sinogram_if_enabled(params):
    if params.use_filter:
        return transform_sinogram(sinogram)
    else:
        return sinogram


def read_image(name):
    image = imread(name, as_grey=True)
    image = rescale(image, scale=0.4, mode='reflect')
    max_image_value = np.max(image)
    if max_image_value > 1:
        image /= 255
    return image


def prepare_instance(params):
    theta = get_moves(params.alpha)
    image = read_image(params.image_name)
    image = make_image_square(image)
    return image, theta


class Scanner:

    def __init__(self, params) -> None:
        self.params = params
        self.image, self.theta = prepare_instance(params)
        self.tomograph = prepare_tomograph(emitters=params.emitters_num, dim=np.max(image.shape))
        self.increased_tomograph = increase_image(tomograph)
        # sinogram =


if __name__ == "__main__":
    image, theta = prepare_instance(params)
    increased_image = increase_image(image)
    tomograph = prepare_tomograph(emitters=params.emitters_num, dim=np.max(image.shape))
    increased_tomograph = increase_image(tomograph)

    sinogram = make_radon(increased_image, increased_tomograph, len(image), theta)
    sinogram_transformed = transform_sinogram_if_enabled(params)
    i_sin = inverse_radon(sinogram_transformed, theta, len(image))

    show_images(image, sinogram, i_sin)

