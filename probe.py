from __future__ import division
import numpy as np
from matplotlib import pyplot as plt
from probes.readUtils import read_flat
from probes.readUtils import openHDF5file, getHDF5params
from probes.readUtils import readHDF5t_100, readHDF5t_101
import h5py
import ctypes


class NeuralProbe(object):

    def __init__(self, num_channels, spike_delay, spike_peak_duration,
                 noise_duration, noise_amp_percent, inner_radius,
                 fps, positions_file_path, neighbors_file_path,
                 masked_channels=None):
        self.num_channels = num_channels
        self.spike_delay = spike_delay
        self.spike_peak_duration = spike_peak_duration
        self.noise_duration = noise_duration
        self.noise_amp_percent = noise_amp_percent
        self.fps = fps
        self.positions_file_path = positions_file_path
        self.neighbors_file_path = neighbors_file_path
        self.masked_channels = masked_channels
        self.inner_radius = inner_radius

        self.loadPositions(positions_file_path)
        self.loadNeighbors(neighbors_file_path)

    # Load in neighbor and positions files
    def loadNeighbors(self, neighbors_file_path):
        neighbor_file = open(neighbors_file_path, 'r')
        neighbors = []
        for neighbor in neighbor_file.readlines():
            neighbors.append(np.array(neighbor[:-2].split(',')).astype(int))
        neighbor_file.close()
        # assert len(neighbors) == len(pos)
        self.neighbors = neighbors
        self.max_neighbors = max([len(n) for n in neighbors])

    def loadPositions(self, positions_file_path):
        position_file = open(positions_file_path, 'r')
        positions = []
        for position in position_file.readlines():
            positions.append(np.array(position[:-2].split(',')).astype(int))
        self.positions = np.asarray(positions)
        position_file.close()

    # Show visualization of probe
    def show(self, show_neighbors=[10], figwidth=3):
        xmax, ymax = self.positions.max(0)
        xmin, ymin = self.positions.min(0)
        ratio = ymax / xmax
        plt.figure(figsize=(figwidth, figwidth * ratio))
        for ch in show_neighbors:
            for neighbor in self.neighbors[ch]:
                plt.plot([self.positions[ch, 0], self.positions[neighbor, 0]],
                         [self.positions[ch, 1], self.positions[neighbor, 1]],
                         '--k', alpha=.7)
        plt.scatter(*self.positions.T)
        for i, pos in enumerate(self.positions):
            plt.annotate(i, pos)
        plt.ylim([0, ymax + ymin])
        plt.xlim([0, xmax + xmin])

    def Read(self, t0, t1):
        raise NotImplementedError("The Read function is not implemented for \
            this probe")

    def getChannelsPositions(self, channels):
        channel_positions = []
        for channel in channels:
            if channel >= self.num_channels:
                raise ValueError('Channel Index too big')
            else:
                channel_positions.append(self.positions[channel])
        return channel_positions


class NeuroPixel(NeuralProbe):
    def __init__(self, data_file_path=None, fps=30000, masked_channels=[385]):

        NeuralProbe.__init__(
            self, num_channels=385, spike_delay=5,
            spike_peak_duration=4, noise_duration=3,
            noise_amp_percent=1, fps=fps,
            inner_radius=40,
            positions_file_path='probes/positions_neuropixel',
            neighbors_file_path='probes/neighbormatrix_neuropixel',
            masked_channels=masked_channels)
        self.data_file = data_file_path
        if data_file_path is not None:
            self.d = np.memmap(data_file_path, dtype=np.int16, mode='r')
            assert len(self.d) / self.num_channels == len(self.d) // \
                self.num_channels, 'Data not multiple of channel number'
            self.nFrames = len(self.d) // self.num_channels
        else:
            print('Note: data file not specified, things may break')

    def Read(self, t0, t1):
        return read_flat(self.d, t0, t1, self.num_channels)


class BioCam(NeuralProbe):
    def __init__(self, data_file_path=None, fps=0, masked_channels=[0]):
        self.data_file = data_file_path
        if data_file_path is not None:
            self.d = openHDF5file(data_file_path)
            self.nFrames, sfd, nRecCh, chIndices, file_format = getHDF5params(
                self.d)
            if file_format == 100:
                self.read_function = readHDF5t_100
            else:
                self.read_function = readHDF5t_101
        else:
            print('Note: data file not specified, setting some defaults')
            nRecCh = 4096
            sfd = fps
        NeuralProbe.__init__(self, num_channels=nRecCh, spike_delay=5,
                             spike_peak_duration=4, noise_duration=2,
                             noise_amp_percent=1, fps=sfd,
                             inner_radius=1.5,
                             positions_file_path='probes/positions_biocam',
                             neighbors_file_path='probes/neighbormatrix_biocam',
                             masked_channels=masked_channels)

    def Read(self, t0, t1):
        return self.read_function(self.d, t0, t1, self.num_channels)


class Mea1k(NeuralProbe):
    def __init__(self, data_file_path=None, fps=20000, number_of_frames=4450600,
                 masked_channels=None):

        NeuralProbe.__init__(self, num_channels=69, spike_delay=5,
                             spike_peak_duration=4, noise_duration=2,
                             noise_amp_percent=1, fps=fps,
                             inner_radius=20,
                             positions_file_path='probes/positions_mea1k',
                             neighbors_file_path='probes/neighbormatrix_mea1k',
                             masked_channels=masked_channels)
        self.data_file = data_file_path
        if data_file_path is not None:
            d = h5py.File(data_file_path)
            self.d = d
            mapping = d.get('/mapping/')
            channel_indices = mapping['channel'][:]
            electrodes = mapping['electrode'][:]
            routed = np.array(np.where(electrodes > -1))[0]
            self.channels_indices_routed = channel_indices[routed]
            self.nFrames = number_of_frames
        else:
            print('Note: data file not specified, setting some defaults')

    def Read(self, t0, t1):
        return self.d['/sig'][self.channels_indices_routed,
                              t0:t1].T.ravel().astype(ctypes.c_short)
