# Video Dubber Software Using TTS

A tool to dub videos using text-to-speech (TTS) from subtitle files, with progress saving fucntionality. It's not perfect, so if you have any ideas on any fixes, make a push request!

## Getting started 

Clone the repository: 

```bash
git clone https://github.com/Arduino-USB/video-dubber 
```
Change into the project directory: 

```bash
cd video-dubber
```
Create a python VENV
```bash
python -m venv video_dubber_venv
```
Activate it:
Windows:
```batch
source video_dubber_venv/bin/activate
```
macOS/Linux:
```bash
source video_dubber_venv/bin/activate
```

Install the required Python packages: 
```bash
pip install -r requirements.txt 
```
Run the main script with your desired arguments:
```bash
 python main.py [ARGS] 
```
## Usage Examples 

How to use the script
``` bash
python main.py -p project_name -v video.mp4 -s subtitles.srt --speakers 50 --from_lang en --to_lang ar
```
Note: projects are the folders where all of the data will be saved. If you ran the script with a project name, closed it, and redid it, it would save to the same folder and resume
Passing speakers (# of people that speak) is HIGHLY recommened, becuase otherwsie the program will tryto estimate and mix voices together


## Arguments Summary
	-v, --video: Input video file to dub.
	-s, --subtitles: Subtitle file to use for dubbing. 
	-p, --project: Folder that you want data to be stored in
	--speakers: Amount of people in video (maybe check the cast of a movie to get that)
	--from-lang: The input language code (en -> English)
	--to-lang: The output language (es -> Spanish)
