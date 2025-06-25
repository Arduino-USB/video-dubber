import srt
import os

def parse(file=None):
	if file == None:
		return -1, "Error: no subtitle file provided"

	if not os.path.exists(file):
		return -1, "Error: this subtitle file doesn't exist"
	
	with open(file, "r", encoding="utf-8") as f:
		srt_content = f.read()

	subtitles = list(srt.parse(srt_content))
	
	subs_as_dicts = []
	
	for i in range(len(subtitles)):
		sub = subtitles[i]
		subs_as_dicts.append({
			"text": sub.content,
			"timestamps": {
				"start": str(sub.start),
				"stop": str(sub.end)
			}
		})
	
	return subs_as_dicts
