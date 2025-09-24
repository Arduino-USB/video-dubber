import numpy as np
import os
import parselmouth
from scipy.spatial.distance import cosine
import numpy as np

def get_pitch(file):
	if not file or not os.path.exists(file):
		print(-1, "Error: You must provide a valid path to an audio clip")
		return None

	try:
		# Load audio
		snd = parselmouth.Sound(file)

		# Extract pitch with a safe floor
		pitch = snd.to_pitch(pitch_floor=75, time_step=0.01)  # 75 Hz captures most voices
		pitch_values = pitch.selected_array['frequency']

		# Keep only positive values (non-zero = voiced regions)
		pitch_values = pitch_values[pitch_values > 0]

		if len(pitch_values) == 0:
			print(-1, "No pitch detected in the audio.")
			return None

		# Median gives a robust average
		median_pitch = float(np.median(pitch_values))
		return round(median_pitch, 2)

	except Exception as e:
		print(-1, f"Error while analyzing pitch: {e}")
		return None

