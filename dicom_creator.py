import os
import tempfile
import datetime
import traceback
import matplotlib.pyplot as plt
import pydicom
from PIL import Image
from pydicom.dataset import Dataset, FileDataset
from pydicom.filewriter import correct_ambiguous_vr

from transformer import read_image


def create_dcm_file(image):
    # Create some temporary filenames
    suffix = '.dcm'
    filename_little_endian = tempfile.NamedTemporaryFile(suffix=suffix).name

    print("Setting file meta information...")
    # Populate required values for file meta information
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    file_meta.MediaStorageSOPInstanceUID = "1.2.3"
    file_meta.ImplementationClassUID = "1.2.3.4"

    print("Setting dataset values...")
    # Create the FileDataset instance (initially no data elements, but file_meta
    # supplied)
    ds = FileDataset(filename_little_endian, {},
                     file_meta=file_meta, preamble=b"\0" * 128)

    # Add the data elements -- not trying to set all required here. Check DICOM
    # standard
    ds.PatientName = ""
    ds.PatientID = ""
    ds.PixelRepresentation = 1
    # Set the transfer syntax
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 1
    ds.HighBit = 15
    ds.BitsStored = 16
    ds.BitsAllocated = 16
    ds.SmallestImagePixelValue = str.encode('\x00\x00')
    ds.LargestImagePixelValue = str.encode('\xff\xff')
    ds.Columns = image.shape[0]
    ds.Rows = image.shape[1]    # Set creation date/time
    dt = datetime.datetime.now()
    ds.ContentDate = dt.strftime('%Y%m%d')
    timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
    ds.ContentTime = timeStr
    try:
        if image.max() <= 1:
            image *= 255
            image = image.astype("uint16")
        ds.PixelData = Image.fromarray(image).tobytes()
    except Exception:
        traceback.print_exc()
    print("Writing test file", filename_little_endian)
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds = correct_ambiguous_vr(ds, True)
    ds.save_as(filename_little_endian)
    print("File saved.")

    print("File saved.")
    print('Load file {} ...'.format(filename_little_endian))
    ds = pydicom.dcmread(filename_little_endian)
    print('Remove file {} ...'.format(filename_little_endian))
    os.remove(filename_little_endian)
    return ds


if __name__ == '__main__':
    image = read_image("./examples/Kropka.jpg")
    dcm = create_dcm_file(image)
    file_name = "dcm.dcm"
    pydicom.filewriter.write_file(file_name, dcm)  # extension required
    # dcm.save_as(file_name)
    ds = pydicom.dcmread(file_name)
    array = ds.pixel_array
    plt.imshow(array)
    plt.show()

