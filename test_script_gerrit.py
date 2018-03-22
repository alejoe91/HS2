from hs2 import HSDetection, HSClustering
from probe import BioCam
from datetime import datetime

data_path = '/disk/scratch/mhennig/P91_05_07_17_TestMotionSeq/raw/'
files = ['P91_05_07_17_basicshort_stim1_ctl.brw', 'P91_05_07_17_swn_stim2_ctl.brw', 'P91_05_07_17_motionbandseq0_stim4_ctl.brw']
data_files = [data_path+f for f in files]

# detection parameters
to_localize = True
cutout_start = 10
cutout_end = 30
cutout_length = cutout_end+cutout_start+1
threshold = 18

detect_it = True
sort_it = True

# Detect and localise
if detect_it is True:
    print("detecting...")
    startTime = datetime.now()
    for f in data_files:
        out_file = f.replace('.brw', '')
        print(f, out_file)
        # make a probe object first, and then set up the detector
        Probe = BioCam(f)
        H = HSDetection(Probe, to_localize, cutout_start, cutout_end, threshold,
                    maa=0, maxsl=12, minsl=3, ahpthr=0, out_file_name=out_file,
                    save_all=False)
        H.DetectFromRaw()
        del H
        del Probe
    print('Time taken for detection: ' + str(datetime.now() - startTime))

# cluster everything
if sort_it is True:
    print("reading files for clustering...")
    out_files = [f.replace('.brw', '.bin') for f in data_files]
    C = HSClustering(out_files, cutout_length=cutout_length)
    C.ShapePCA(pca_ncomponents=2, pca_whiten=True)
    print("starting Mean Shift...")
    startTime = datetime.now()
    C.CombinedClustering(alpha=0.4, bandwidth=0.3, bin_seeding=True,
                         min_bin_freq=40, n_jobs=-1)
    sorted_files = [f.replace('.brw', '_clustered.hdf5') for f in data_files]
    print('Time taken for sorting: ' + str(datetime.now() - startTime))
C.SaveHDF5(sorted_files)