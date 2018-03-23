import os
import tempfile
import datetime
import traceback

import pydicom
from PIL import Image
from pydicom.dataset import Dataset, FileDataset


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
    ds.is_implicit_VR = True

    # Set creation date/time
    dt = datetime.datetime.now()
    ds.ContentDate = dt.strftime('%Y%m%d')
    timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
    ds.ContentTime = timeStr
    try:
        ds.PixelData = Image.fromarray(image).tobytes()
    except Exception:
        traceback.print_exc()
    print("Writing test file", filename_little_endian)
    # pydicom.filewriter.correct_ambiguous_vr(ds, True)
    ds.save_as(filename_little_endian)
    print("File saved.")

    # Write as a different transfer syntax XXX shouldn't need this but pydicom
    # 0.9.5 bug not recognizing transfer syntax
    # ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    # ds.is_little_endian = True
    # ds.is_implicit_VR = True
    # pydicom.filewriter.correct_ambiguous_vr(ds, True)
    # # reopen the data just for checking
    # print("Writing test file", filename_little_endian)
    #
    # ds.save_as(filename_little_endian)
    print("File saved.")
    print('Load file {} ...'.format(filename_little_endian))
    ds = pydicom.dcmread(filename_little_endian)
    # print(ds)

    # remove the created file
    print('Remove file {} ...'.format(filename_little_endian))
    os.remove(filename_little_endian)
    return ds
