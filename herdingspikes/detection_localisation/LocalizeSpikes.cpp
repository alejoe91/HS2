#include "LocalizeSpikes.h"

namespace LocalizeSpikes {

struct CustomLessThan {
  bool operator()(tuple<int, int> const &lhs,
                  tuple<int, int> const &rhs) const {
    return std::get<1>(lhs) < std::get<1>(rhs);
  }
};

tuple<float, float> centerOfMass(deque<tuple<int, int>> centered_amps) {
  /*Calculates the center of mass of a spike to calculate where it occurred
     using a weighted average.

     Parameters
     ----------
     centered_amps: deque<tuple<int, int>>
     A deque containing all non-zero amplitudes and their neighbors. Used for
     center of mass.

     Returns
     -------
     position: tuple<float, float>
     An X and Y coordinate tuple that corresponds to where the spike occurred.
   */
  // int curr_amp;
  float X = 0;
  float Y = 0;
  int X_numerator = 0;
  int Y_numerator = 0;
  int denominator = 0;
  int X_coordinate;
  int Y_coordinate;
  int channel;
  int weight; // contains the amplitudes for the center of mass calculation.
              // Updated each localization
  int centered_amps_size = centered_amps.size();

  for (int i = 0; i < centered_amps_size; i++) {
    weight = get<1>(centered_amps.at(i));
    channel = get<0>(centered_amps.at(i));
    X_coordinate = Parameters::channel_positions[channel][0];
    Y_coordinate = Parameters::channel_positions[channel][1];
    if (weight < 0) {
      cout << "\ncenterOfMass::weight < 0 - this should not happen\n";
    }
    X_numerator += weight * X_coordinate;
    Y_numerator += weight * Y_coordinate;
    denominator += weight;
  }

  X = (float)(X_numerator) / (float)(denominator);
  Y = (float)(Y_numerator) / (float)(denominator);

  if ((denominator == 0)) //| (X>10 & X<11))
  {
    cout << "\ncenterOfMass::denominator == 0 - This should not happen\n";
    for (int i = 0; i < centered_amps_size; i++) {
      channel = get<0>(centered_amps.at(i));
      cout << " " << get<1>(centered_amps.at(i)) << " "
           << Parameters::channel_positions[channel][0] << "\n";
    }
    cout << "\n";
  }

  return make_tuple(X, Y);
}

tuple<float, float> localizeSpike(Spike spike_to_be_localized) {
  /*Estimates the X and Y position of where a spike occured on the probe.

     Parameters
     ----------
     spike_to_be_localized: Spike
     The spike that will be used to determine where the origin of the spike
     occurred.

     Returns
     -------
     position: tuple<float, float>
     An X and Y coordinate tuple that corresponds to where the spike occurred.
   */
  deque<tuple<int, int>> amps;
  int curr_largest_amp = INT_MIN; // arbitrarily small to make sure that it is
                                  // immediately overwritten
  int curr_neighbor_channel;
  int curr_amp;

  int amp_cutout_size = spike_to_be_localized.amp_cutouts.size();
  int neighbor_frame_span = Parameters::spike_delay * 2 + 1;
  int neighbor_count = amp_cutout_size / neighbor_frame_span;
  int matrix_offset = 0;

  for (int i = 0; i < neighbor_count; i++) {
    curr_neighbor_channel =
        Parameters::inner_neighbor_matrix[spike_to_be_localized.channel][i];
    if (Parameters::masked_channels[curr_neighbor_channel] != 0) {
      for (int j = 0; j < neighbor_frame_span; j++) {
        curr_amp = spike_to_be_localized.amp_cutouts.at(j + matrix_offset);
        if (curr_amp > curr_largest_amp) {
          curr_largest_amp = curr_amp;
        }
      }
      amps.push_back(make_tuple(curr_neighbor_channel, curr_largest_amp));
      curr_largest_amp = INT_MIN;
      matrix_offset += neighbor_frame_span;
    }
  }
  // Attention, median is really min - make sure all ampltudes are positive!
  int do_correction = 1;
  int correct = 0;
  int amps_size = amps.size();
  if (do_correction == 1) {
    sort(begin(amps), end(amps), CustomLessThan()); // sort the array
    // Find median of array
    // if(amps_size % 2 == 0) {
    //         correct = (get<1>(amps.at(amps_size/2)) +
    //         get<1>(amps.at(amps_size/2 + 1)))/2;
    // }
    // else {
    //         correct = get<1>(amps.at(amps_size/2));
    // }
    correct = get<1>(amps.at(0))-1;
  }
  // Correct amplitudes
  deque<tuple<int, int>> centered_amps;
  if (amps_size != 1) {
    for (int i = 0; i < amps_size; i++) {
      centered_amps.push_back(
          make_tuple(get<0>(amps.at(i)), get<1>(amps.at(i)) - correct));
    }
  } else {
    centered_amps.push_back(amps.at(0));
  }

  int centered_amps_size = centered_amps.size();
  if (centered_amps_size == 0) {
    cout << "\nThis should not happen\n";
    centered_amps = amps;
  }
  tuple<float, float> position = centerOfMass(centered_amps);
  amps.clear();
  centered_amps.clear();
  return position;
}
}