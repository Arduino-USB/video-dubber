from resemblyzer import VoiceEncoder, preprocess_wav
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
from kneed import KneeLocator
from tts_manager import tts, get_voices
import matplotlib.pyplot as plt
from pydub import AudioSegment
import noisereduce as nr
import torchaudio
import torch
import parselmouth
import numpy as np
import ffmpeg
import uuid
import json
import os


def get_best_voice_from_voices(voices=None, pitch=None):
	if voices is None:
		print(-1, "You must provide a list of dictionaries of voices and pitches")
		return None

	if pitch is None:
		print(-1, "You must provide a target pitch")
		return None

	winner_index = 0
	winner_distance = abs(pitch - voices[0]["pitch"])

	for i in range(1, len(voices)):
		current_distance = abs(pitch - voices[i]["pitch"])
		if current_distance < winner_distance:
			winner_distance = current_distance
			winner_index = i

	return {
		"index": winner_index,
		"id": voices[winner_index]["id"]
	}

def get_segment_by_filename(segment_files, filename):
	for i in range(len(segment_files)):
		if segment_files[i].get("file") == filename:
			return segment_files[i]
	return None


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


def extract_audio(video_path, clean=False):
	print("[extract_audio] Starting audio extraction")

	# Step 1: Extract audio with ffmpeg
	raw_audio_path = str(uuid.uuid4()) + "_raw.wav"
	print(f"[extract_audio] Extracting raw audio to {raw_audio_path}")
	ffmpeg.input(video_path).output(
		raw_audio_path,
		format='wav',
		acodec='pcm_s16le',
		ar='16000',
		ac=1,
		vn=None
	).run(overwrite_output=True, quiet=True)

	if clean:
		print("[extract_audio] Loading raw audio for noise reduction")
		waveform, sr = torchaudio.load(raw_audio_path)
		waveform_np = waveform.numpy()[0]  # assuming mono channel

		print("[extract_audio] Applying noise reduction")
		reduced_noise = nr.reduce_noise(y=waveform_np, sr=sr)

		clean_path = str(uuid.uuid4()) + "_clean.wav"
		torchaudio.save(clean_path, torch.tensor(reduced_noise).unsqueeze(0), sr)

		print("[extract_audio] Loading cleaned audio into AudioSegment")
		audio = AudioSegment.from_file(clean_path)

		# Cleanup temp clean file
		os.remove(clean_path)

	else:
		print("[extract_audio] Loading raw audio into AudioSegment")
		audio = AudioSegment.from_file(raw_audio_path)

	# Cleanup raw audio file in all cases
	os.remove(raw_audio_path)

	print("[extract_audio] Done")
	return audio



def get_voice_index_by_id(voices=None, target=None):

	if voices == None or target == None:
		print(-1, "Error, both voices list and target id must be given")	
		return -2
		
	for i in range(len(voices)):
		if voices[i]["id"] == target:
			return i

	return -1


def burn_audio_stage(audio_filename=None, video_source=None, video_filename=None):
	if not audio_filename or not video_source or not video_filename:
		raise ValueError("audio_filename, video_source, and video_filename must all be provided")

	print("[burn_audio_stage] Burning audio into new file")
	video_in = ffmpeg.input(video_source)
	audio_in = ffmpeg.input(audio_filename)

	# Combine streams without manual -map, keep video codec, encode audio as AAC
	ffmpeg.output(
		video_in['v'], audio_in['a'],
		video_filename,
		vcodec='copy',
		acodec='aac',
		strict='experimental'
	).overwrite_output().run()
		
	print("[burn_audio_stage] Done")




def audio_stage(audio=None, tts_file_map=None):	
	if audio is None:
		print(-1, "You must provide an AudioSegment object to use as a base")
		return -1
	
	if tts_file_map is None:
		print(-1, "You must provide a tts file map, which has names of tts output files along with timestamps they belong in")
		return -1
	
	print("[audio_stage] Combining TTS output")
	for i in range(len(tts_file_map)):
		item = tts_file_map[i]
		filename = list(item.keys())[0]
		timing = item[filename]

		tts_audio = AudioSegment.from_wav(filename)
		start = timing['start']
		stop = timing['stop']

		audio = audio[:start] + tts_audio + audio[stop:]

	print("[audio_stage] Saving audio as dubbed_audio.wav")
	
	audio.export("dubbed_audio.wav", format="wav")

def segment_stage(audio=None, subs=None, video_path=None, index=0):
	segments=[]
	print("[segment_stage] Splitting segments")
	

	for i in range(index, len(subs)):
		start = subs[i]["timestamps"]["start"]
		stop = subs[i]["timestamps"]["stop"]
		segment = audio[start:stop]
		segment_file = f"segment_{i}.wav"
		elapsed = (stop - start) / 1000

		if elapsed > 0.5:
			print(f"[segment_stage] Saving file {segment_file}")
			segment.export(segment_file, format="wav")
			segments.append({
				"file" : segment_file,
				"timestamps": {"start" : start, "stop" : stop},
				"text" : subs[i]["text"]
			})


	with open("stage0.output", "w") as f:
		json.dump({"segments" : segments}, f)
	return segments


import os
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from kneed import KneeLocator
from resemblyzer import VoiceEncoder, preprocess_wav

def voices_stage(segment_files=[], valid_files=[], save_file=False, index=0, eps=0.15, speakers=None):
	encoder = VoiceEncoder()

	if not segment_files:
		print(f"[voices_stage] Loading segment files")
		all_files = os.listdir()
		for f in all_files:
			if f.startswith("segment_") and f.endswith(".wav"):
				segment_files.append(f)
	else:
		print("[voices_stage] segment_files already exists, skipping")

	embeddings = []
	start_index = index

	for i in range(start_index, len(segment_files)):
		wav = preprocess_wav(segment_files[i])
		emb = encoder.embed_utterance(wav)
		embeddings.append(emb)
		valid_files.append(segment_files[i])

	if start_index > 0:
		if os.path.exists("embeddings.npy"):
			embeddings = np.load("embeddings.npy")
			print("[voices_stage] Loaded cached embeddings")
		else:
			print("[voices_stage] Re-embedding all valid files")
			embeddings = []
			for f in valid_files:
				wav = preprocess_wav(f)
				emb = encoder.embed_utterance(wav)
				embeddings.append(emb)
			embeddings = np.array(embeddings)
			if save_file:
				np.save("embeddings.npy", embeddings)
				print("[voices_stage] Saved re-embedded embeddings")

	print("[voices_stage] Normalizing embeddings")
	embeddings = normalize(np.array(embeddings))

	if speakers == None:
		# Estimate number of speakers with improved elbow logic
		print("[voices_stage] Estimating number of speakers")

		max_clusters = min(50, len(embeddings))
		inertias = []
		K = range(1, max_clusters + 1)

		for k in K:
			km = KMeans(n_clusters=k).fit(embeddings)
			inertias.append(km.inertia_)

		knee = KneeLocator(K, inertias, curve="convex", direction="decreasing")
		estimated_k = knee.elbow
		if estimated_k is None:
			print("[voices_stage] No elbow found, using fallback")
			estimated_k = 12  # fallback slightly higher
		else:
		# Bias up slightly unless already high
			estimated_k += 2
			if estimated_k > len(embeddings):
				estimated_k = len(embeddings)
			print(f"[voices_stage] Adjusted speaker count: {estimated_k}")
	else:
		estimated_k = speakers
		print(f"[voices_stage] Speakers passed in: {estimated_k}")

	print(f"[voices_stage] Estimated speaker count: {estimated_k}")

	labels = KMeans(n_clusters=estimated_k).fit_predict(embeddings)

	clusters = {}
	for i in range(len(labels)):
		label = str(labels[i])
		file = valid_files[i]
		if label not in clusters:
			clusters[label] = []
		clusters[label].append(file)

	with open("stage1.output", "w") as f:
		json.dump({"clusters": clusters}, f)

	return clusters


def tts_stage(segment_files=None, subs=None, clusters=None, tts_lang=None, save_file=True, index_i=0, index_j=0, voices=get_voices(), tts_map=[]):

	
	if segment_files == None or subs == None or clusters == None or tts_lang == None:
		print("[tts_stage] [ERROR]: segment_files, subs, clusters, tts_lang must all be passed")		
		

	for i in range(index_i, len(clusters)):
		
		if not voices:
			print("[tts_stage] [ERROR]: No voices left to assign")
			break

		voice_to_use_object = get_best_voice_from_voices(voices=voices, pitch=get_pitch(clusters[str(i)][0]))
		print(f"[tts_stage] voice_to_use_object: {voice_to_use_object}")
		voices.pop(voice_to_use_object["index"])
				
		print(f"[tts_stage] Generating TTS for cluster index {i}")
		print(f"[tts_stage] Voice ID: {voice_to_use_object['id']}")
		

		
		start_j = index_j if i == index_i else 0

		for j in range(start_j, len(clusters[str(i)])):
			segment_file = clusters[str(i)][j]
			segment_file_info = get_segment_by_filename(segment_files=segment_files, filename=segment_file)
			print(f"[tts_stage] [for-loop] Segment file object {segment_file_info}")
		
			tts_output_file = "tts_output_" + str(i) + str(j) + ".wav"

	
			tts(
				text=segment_file_info["text"], 
				output_file=tts_output_file, 
				lang=tts_lang, 
				speaker_index=voice_to_use_object["id"]
			)
			
			timestamps = segment_file_info["timestamps"]
			print(f"[tts_stage] [for-loop] Timestamps: {timestamps}")
			tts_map.append({tts_output_file: timestamps})
			
			if save_file:
				save_data = {
					"index_i": i,
					"index_j": j + 1,
					"voices": voices,
					"tts_lang": tts_lang,
					"tts_map": tts_map
				}
				with open("stage2.json", "w") as f:
					json.dump(save_data, f)
				print(f"[tts_stage] Saved progress at cluster {i}, segment {j}")
		
		# reset j after each cluster
		index_j = 0
	with open("stage2.output", "w") as f:
		json.dump({"tts_map" : tts_map}, f)
	return tts_map

	
		
