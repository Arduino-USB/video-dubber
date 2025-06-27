#from resemblyzer import VoiceEncoder, preprocess_wav
#from pathlib import Path
import numpy as np
import os
import parselmouth

def get_pitch(file=None):

	if file is None:
		return -1, "Error: You must provide with a path to an audio clip"
  
	if not os.path.exists(file):
		return -1, "Error: The path provided for the audio clip does not exist"

	snd = parselmouth.Sound(file)
	pitch = snd.to_pitch()
	pitch_values = pitch.selected_array['frequency']
	pitch_values = pitch_values[(pitch_values > 50) & (pitch_values < 500)]

	if len(pitch_values) == 0:
		return None

	return float(np.median(pitch_values))













#import librosa
#
#def get_pitch(file=None):
#
#	if file is None:
#		return -1, "Error: You must provide with a path to an audio clip"
#    
#	if not os.path.exists(file):
#		return -1, "Error: The path provided for the audio clip does not exist"
#
#	y, sr = librosa.load(file)
#	pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
#	pitch_values = pitches[magnitudes > np.median(magnitudes)]
#	if len(pitch_values) == 0:
#	    return None
#	return round(float(pitch_values.mean()))

#def get_gender(file=None):
#    if file is None:
#        return -1, "Error: You must provide with a path to an audio clip"
#    
#    if not os.path.exists(file):
#        return -1, "Error: The path provided for the audio clip does not exist"
#
#    [Fs, x] = audioBasicIO.read_audio_file(file)
#
#    # Convert to mono if stereo
#    if x.ndim > 1:
#        x = x.mean(axis=1)
#
#    F = audioFeatureExtraction.feature_extraction(x, Fs, 0.050 * Fs, 0.025 * Fs)
#    
#    result, P, classNames = aT.file_classification(file, "gender_model", "svm")
#    
#    return result, classNames[result]



def cosine_similarity(a, b):
	return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def same_speaker(audio1=None, audio2=None):

	if audio1 == None or audio2 == None:
		return -1, "Error: You must provide 2 audio clip paths"

	if not os.path.exists(audio1) or not os.path.exists(audio2):
		return -1, "Error: You must provide with vaild paths for both audio clips"

	wav_fpath1 = audio1
	wav_fpath2 = audio2
	
	# Load and preprocess
	wav1 = preprocess_wav(Path(wav_fpath1))
	wav2 = preprocess_wav(Path(wav_fpath2))
	
	# Initialize encoder
	encoder = VoiceEncoder()
	
	# Get embeddings
	embed1 = encoder.embed_utterance(wav1)
	embed2 = encoder.embed_utterance(wav2)
	
	# Compute cosine similarity
	similarity = cosine_similarity(embed1, embed2)
	print(f"Similarity: {similarity}")
	
	# You can decide a threshold, for example >0.75 means same speaker
	if similarity > 0.75:
		return True
	else:
		return False

