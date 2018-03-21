import pydicom
from pydicom.data import get_testdata_files
import matplotlib.pyplot as plt
# get some test data
filename = get_testdata_files("CT_small.dcm")[0]
ds = pydicom.dcmread(filename)
pixel_bytes = ds.pixel_array
print(ds.PatientName)

print(ds[0x10,0x10].value)

ds.PatientID = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
ds.SeriesNumber = 5
print(ds)
ds[0x10,0x10].value = 'Test'

fig, ax = plt.subplots(1, 1, figsize=(8, 8))
ax.imshow(pixel_bytes, cmap=plt.cm.Greys_r)
plt.show()
pydicom.filewriter.write_file("my_dicom.dic", ds) # extension required