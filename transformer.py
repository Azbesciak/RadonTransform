import traceback

import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fftfreq, fft, ifft
from skimage.filters import gaussian
from skimage.io import imread
from skimage.transform import rescale, rotate
import warnings
from bresenham import bresenham

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

image_indx = 8


class TransformSnapshot:

    def __init__(self, sinogram=None, i_sin=None) -> None:
        self.sinogram = sinogram
        self.i_isn = i_sin


class Parameters:

    def __init__(self, alpha, emitters_num, use_filter, image_name, use_gauss=True, use_omega=False) -> None:
        self.alpha = alpha
        self.emitters_num = emitters_num
        self.use_filter = use_filter
        self.image_name = image_name
        self.use_gauss = use_gauss
        self.use_omega = use_omega

    def set_values(self, alpha, emitters_num, use_filter, image_name, use_gauss=True, use_omega=False):
        if alpha <= 0:
            raise Exception("Alpha must be positive")
        if emitters_num <= 0:
            raise Exception("Emitters num must be positive")
        if image_name is None:
            raise Exception("Image was not selected")
        self.alpha = alpha
        self.emitters_num = emitters_num
        self.use_filter = use_filter
        self.image_name = image_name
        self.use_gauss = use_gauss
        self.use_omega = use_omega


params = Parameters(180 / 360, 800, True, images[image_indx])


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
        target[:, start + to_write[0]::distance] = filter[i]


def prepare_increased_tomograph(emitters, dim, use_gauss):
    dim = int(dim * np.sqrt(2))
    return prepare_tomograph(emitters, dim, use_gauss)


def prepare_tomograph(emitters, dim, use_gauss):
    if emitters > dim:
        warnings.warn("emmiters num was bigger than image dim - used smaller")
    emitters = np.min((emitters, dim))
    tomo = np.zeros((dim, dim))
    distance = int(dim / emitters)
    start = int(np.ceil(distance / 2))
    create_filter_at(tomo, start, distance, [1])
    if use_gauss:
        tomo = gaussian(tomo)
    tomo /= tomo.max()
    tomo = np.rot90(tomo)
    return tomo


def get_intersection(rotation, image, tomograph, real_dim):
    rotation += 90
    rotated = rotate(tomograph, rotation)
    common_part = rotated * image
    common_rotated_again = rotate(common_part, -rotation)
    column_avg = [sum(q) / real_dim for q in common_rotated_again]
    return column_avg


def make_radon(increased_image, increased_tomograph, real_dim, theta, on_change=None):
    res = np.zeros((len(theta), len(increased_tomograph)))
    for i, rotation in enumerate(theta):
        res[i] = get_intersection(rotation, increased_image, increased_tomograph, real_dim)
        if on_change is not None:
            on_change(si=res, iter=i)
    return res


def transform_sinogram(params, sinogram):
    sinogram = np.rot90(sinogram, k=1)
    freqs = sinogram.shape[0]
    projection_size_padded = \
        max(64, int(2 ** np.ceil(np.log2(2 * freqs))))
    pad_width = ((0, projection_size_padded - freqs), (0, 0))
    img = np.pad(sinogram, pad_width, mode='constant', constant_values=0)
    f = fftfreq(projection_size_padded).reshape(-1, 1)
    omega = 2 * np.pi * f
    fourier_filter = 2 * np.abs(f)
    if params.use_omega:
        fourier_filter *= np.cos(omega)
    projection = fft(img, axis=0) * fourier_filter
    radon_filtered = np.real(ifft(projection, axis=0))
    radon_filtered = radon_filtered[:freqs, :]
    return np.rot90(radon_filtered, k=-1)


def norm(mat):
    mat_min = mat.min()
    mat -= mat_min
    mat_max = mat.max()
    if mat_max > 0:
        mat /= mat_max
    return mat


def inverse_radon(sigmoid, rotations, output_size, on_change=None):
    reconstructed = increase_image(np.zeros((output_size, output_size)))
    reconstr_len = len(reconstructed)
    start = (reconstr_len - output_size) // 2
    end = start + output_size
    rotations_len = len(rotations)
    result = reconstructed[start:end, start:end]
    for i in range(rotations_len):
        temp = np.array([sigmoid[i], ] * reconstr_len)
        temp = make_image_square(temp)
        reconstructed += rotate(temp, rotations[i])
        result = reconstructed[start:end, start:end]
        if on_change is not None:
            on_change(isi=result, iter=i)

    result = norm(result)
    return result


def get_moves(a):
    return [a * i for i in range(int(np.ceil(180 / a)))]


def show_images(original, sinogram, reconstructed):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(8, 8))
    ax1.imshow(original, cmap=plt.cm.Greys_r)
    ax2.imshow(sinogram, cmap=plt.cm.Greys_r)
    ax3.imshow(reconstructed, cmap=plt.cm.Greys_r)
    plt.show()


def transform_sinogram_if_enabled(params, sinogram):
    if params.use_filter:
        return transform_sinogram(params, sinogram)
    else:
        return sinogram


def read_image(name):
    image = imread(name, as_grey=True)
    return normalize_img(image)


def normalize_img(image):
    image = rescale(image, scale=0.4, mode='reflect')
    max_image_value = np.max(image)
    if max_image_value > 1:
        image /= 255
    return image


def prepare_instance(params, image=None):
    theta = get_moves(params.alpha)
    if image is None:
        image = read_image(params.image_name)
    image = make_image_square(image)
    return image, theta


class Scanner:
    update_time = 0.2

    def __init__(self, params, plot, image, on_finish=lambda: None) -> None:
        self.params = params
        self.image, self.theta = prepare_instance(params, image)
        self.increased_image = increase_image(self.image)
        self.increased_tomograph = prepare_increased_tomograph(emitters=params.emitters_num,
                                                               dim=np.max(self.image.shape),
                                                               use_gauss=params.use_gauss)
        self.sinogram = None
        self.sinogram_transformed = None
        self.i_sin = None
        self.refresh_sinogram = self.refresh_isin = False
        self.on_finish = on_finish
        self.plot = plot
        self.snapshots = [TransformSnapshot() for _ in self.theta]

    def get_snapshot(self, i):
        try:
            i = int(i / 99 * (len(self.theta) - 1))
            snap = self.snapshots[i]
            self.i_sin = snap.i_isn
            self.sinogram = snap.sinogram
            self.refresh_sinogram = True
            self.refresh_isin = True
        except Exception:
            traceback.print_exc()

    def assign(self, si=None, isi=None, tisi=None, iter=None):
        if si is not None:
            if self.sinogram is None:
                self.sinogram = si
                self.plot.on_sinogram(si)
            else:
                self.sinogram = si
            if iter is not None:
                self.snapshots[iter].sinogram = np.array(si)
            self.refresh_sinogram = True
        if isi is not None:
            if self.i_sin is None:
                self.i_sin = isi
                self.plot.on_isinogram(isi)
            else:
                self.i_sin = isi
            if iter is not None:
                self.snapshots[iter].i_isn = np.array(isi)
            self.refresh_isin = True
        if tisi is not None:
            self.sinogram_transformed = tisi

    def watch_changes(self):
        self.plot.on_new_scan(self.image)
        sinogram = make_radon(self.increased_image, self.increased_tomograph,
                              len(self.image), self.theta, on_change=self.assign)
        sinogram_transformed = transform_sinogram_if_enabled(self.params, sinogram)
        self.assign(tisi=sinogram_transformed)
        i_sin = inverse_radon(sinogram_transformed, self.theta, len(self.image), on_change=self.assign)
        self.on_finish()


if __name__ == "__main__":
    image, theta = prepare_instance(params)
    increased_image = increase_image(image)
    increased_tomograph = prepare_increased_tomograph(emitters=params.emitters_num,
                                                      dim=np.max(image.shape), use_gauss=params.use_gauss)
    sinogram = make_radon(increased_image, increased_tomograph, len(image), theta)
    sinogram_transformed = transform_sinogram_if_enabled(params, sinogram)
    i_sin = inverse_radon(sinogram_transformed, theta, len(image))

    show_images(image, sinogram, i_sin)
