import math
import json
from pathlib import Path
import subprocess
from .graphics import frame, caption_layout


def render(script, timeline, config, out):
    # Layout checks happen before expensive encoding.
    layouts=[{'scene':i,'lines':caption_layout(c['text'])[0],'font_px':caption_layout(c['text'])[1]*2,'safe_box':[88,1536,992,1784]} for i,c in enumerate(timeline)]
    (out/'caption-layout.json').write_text(json.dumps(layouts,indent=2))
    duration=timeline[-1]['end']
    # Measure before encoding: one-pass loudnorm can overshoot on short speech.
    analysis=subprocess.run(['ffmpeg','-hide_banner','-i',str(out/'narration.wav'),'-af','loudnorm=I=-16:TP=-3:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
    measured=json.loads(analysis[analysis.rfind('{'):analysis.rfind('}')+1])
    (out/'audio-normalization.json').write_text(json.dumps(measured,indent=2)+'\n')
    normalization=('loudnorm=I=-16:TP=-3:LRA=7:linear=true'
        +':measured_I='+measured['input_i']+':measured_TP='+measured['input_tp']
        +':measured_LRA='+measured['input_lra']+':measured_thresh='+measured['input_thresh']
        +':offset='+measured['target_offset']+',alimiter=limit=0.794328:level=false')
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(config.fps),'-i','pipe:0','-i',str(out/'narration.wav'),'-vf','scale=1080:1920:flags=lanczos','-af',normalization,'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart','-shortest',str(out/'preview.mp4')]
    with (out/'render.log').open('w') as log:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        try:
            for i in range(math.ceil(duration*config.fps)):
                image=frame(script,timeline,i/config.fps)
                process.stdin.write(image.tobytes())
            process.stdin.close()
            if process.wait()!=0:raise RuntimeError('FFmpeg rendering failed; see render.log')
        except BaseException:
            process.kill();process.wait();raise
    for index,c in enumerate(timeline):
        frame(script,timeline,(c['start']+c['end'])/2).save(out/f'scene-{index+1}.png')
    frame(script,timeline,duration-.1).save(out/'final-frame.png')
