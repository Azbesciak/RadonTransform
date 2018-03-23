import pydicom
from pydicom.data import get_testdata_files
import matplotlib.pyplot as plt
# get some test data
# filename = get_testdata_files("CT_small.dcm")[0]
filename = "my_dicom.dic"
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

# (0008, 0020) Study Date                          DA: '20040119'
# (0008, 0012) Instance Creation Date              DA: '20040119'
# (0008, 0013) Instance Creation Time              TM: '072731'
# (0008, 0014) Instance Creator UID                UI: 1.3.6.1.4.1.5962.3
# (0010, 0010) Patient's Name                      PN: 'CompressedSamples^CT1'
# (0010, 0020) Patient ID                          LO: 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# (0010, 0030) Patient's Birth Date                DA: ''
# (0010, 0040) Patient's Sex                       CS: 'O'
# (0010, 1010) Patient's Age                       AS: '000Y'
# (0010, 1030) Patient's Weight                    DS: "0.000000"
# (0020, 4000) Image Comments                      LT: 'Uncompressed'