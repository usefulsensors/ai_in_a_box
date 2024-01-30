"""Class for high pass filtering of the input stream."""
import numpy as np
from scipy.signal import lfilter, butter


class ChunkHPFilter:
    """Filters chunks of data, uses scipy lfilter method."""

    def __init__(self, fc=100., order=6, rate=16000.):
        # Design coefficients for 6th order high-pass filter suitable for speech.
        self.b, self.a = butter(N=order, Wn=fc, btype='highpass', fs=rate)
        self.zi = None
        self.reset()

    def run(self, chunk: np.ndarray) -> np.ndarray:
        """Returns filtered chunk of arbitrary length."""
        # Apply the filter to the data chunk using the initial conditions.
        filtered_chunk, self.zi = lfilter(self.b, self.a, chunk, zi=self.zi)

        return filtered_chunk

    def reset(self) -> None:
        # Resets the lfilter zi value to zero.  Use after a chunk drop to prevent
        # unexpected filter output.
        self.zi = np.zeros(max(len(self.a), len(self.b)) - 1)
