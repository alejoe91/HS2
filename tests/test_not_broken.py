import unittest
import herdingspikes as hs
import matplotlib.pyplot as plt
import os
from shutil import rmtree


# raw data location
DATA = "data/visapy_data.npy"

# detection parameters
FILEDIR = "results/"
FILENAME = "ProcessedSpikes_visapy"


class TestHS(unittest.TestCase):
    """These tests are only designed to check if detection and clustering
    run smoothly and no bugs were introduced that break down the current pipeline
    in the most basic sense. They don't check for correctness of the result and
    they don't check for particular features."""

    @classmethod
    def setUpClass(cls):
        rmtree(FILEDIR)
        os.makedirs(FILEDIR, exist_ok=True)

    def setUp(self):
        os.makedirs(FILEDIR, exist_ok=True)
        self.Probe = hs.probe.HierlmannVisapyEmulationProbe(
            DATA, inner_radius=60, neighbor_radius=100
        )
        self.H = hs.HSDetection(
            self.Probe,
            out_file_name=FILENAME,
            file_directory_name=FILEDIR,
            left_cutout_time=0.45,
            right_cutout_time=1.12,
        )

    def test_01_run_detection(self):
        self.H.DetectFromRaw(load=True)
        fname = os.path.join(FILEDIR, FILENAME)
        self.assertTrue(os.path.isfile(fname + ".bin"))

    def test_02_plots_post_detection(self):
        self.H.LoadDetected()
        self.Probe.show()
        plt.savefig(os.path.join(FILEDIR, "probe.png"))
        plt.figure()
        self.H.PlotTracesChannels(145, window_size=102)
        plt.savefig(os.path.join(FILEDIR, "traces.png"))
        plt.figure()
        self.H.PlotAll(invert=True)
        plt.savefig(os.path.join(FILEDIR, "locations.png"))

    def test_03_run_clustering(self):
        self.H.LoadDetected()
        self.C = hs.HSClustering(self.H)
        self.C.ShapePCA(pca_ncomponents=2, pca_whiten=True)

        self.C.CombinedClustering(
            alpha=4, bandwidth=5.0, bin_seeding=False, n_jobs=4, cluster_subset=1000
        )
        fname = os.path.join(FILEDIR, "sorted.hdf5")
        self.C.SaveHDF5(fname)
        self.assertTrue(os.path.isfile(fname))

        self.C.PlotShapes(range(2))
        plt.savefig(os.path.join(FILEDIR, "cl_shapes.png"))

        self.C.PlotNeighbourhood(1, radius=6, alpha=0.8)
        plt.savefig(os.path.join(FILEDIR, "cl_neigh.png"))