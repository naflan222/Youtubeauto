"""Offline CPU-only speech; captions use the measured scene audio intervals."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
import wave


def prepare_voice(cache=Path('.cache/voice')):
    lock = json.loads(Path('voice.lock.json').read_text())
    cache.mkdir(parents=True, exist_ok=True)
    for item in lock['files']:
        path = cache / item['name']
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            temporary = path.with_suffix(path.suffix + '.download')
            with urllib.request.urlopen(item['url'], timeout=120) as response:
                with temporary.open('wb') as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != item['sha256']:
                temporary.unlink()
                raise ValueError('Voice checksum mismatch; refusing unverified model')
            temporary.replace(path)
    return cache / 'en_US-ljspeech-medium.onnx'


def wav_seconds(path):
    with wave.open(str(path)) as audio:
        return audio.getnframes() / audio.getframerate()


def narrate(script, config, out):
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    import onnxruntime
    onnxruntime.set_default_logger_severity(3)
    voice = PiperVoice.load(str(prepare_voice()), use_cuda=False)
    raw_paths = []
    for index, scene in enumerate(script['scenes']):
        path = out / f'raw-{index}.wav'
        with wave.open(str(path), 'wb') as wav:
            voice.synthesize_wav(scene['narration'], wav, syn_config=SynthesisConfig(length_scale=1.35))
        raw_paths.append(path)
    raw_total = sum(wav_seconds(path) for path in raw_paths)
    target = min(config.max_duration - 1, max(config.min_duration + 1, 32))
    gap = 0.22
    speed = raw_total / (target - gap * len(raw_paths))
    if not .65 <= speed <= 1.5:
        raise ValueError('Script needs editorial revision to meet natural pacing and duration')
    timeline, now, pcm = [], 0.0, bytearray()
    rate = 22050
    for index, (scene, raw) in enumerate(zip(script['scenes'], raw_paths)):
        path = out / f'scene-{index}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', f'atempo={speed}', '-ar', str(rate), '-ac', '1', '-c:a', 'pcm_s16le', str(path)], check=True)
        with wave.open(str(path)) as audio:
            frames = audio.readframes(audio.getnframes())
        duration = len(frames) / (rate * 2)
        timeline.append({'start': now, 'speech_end': now + duration, 'end': now + duration + gap, 'text': scene['narration'], 'visual': scene['visual'], 'scene': index})
        pcm.extend(frames)
        pcm.extend(b'\0\0' * round(rate * gap))
        now += duration + gap
    with wave.open(str(out / 'narration.wav'), 'wb') as audio:
        audio.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        audio.writeframes(pcm)
    (out / 'timeline.json').write_text(json.dumps(timeline, indent=2))
    def stamp(seconds):
        ms = round(seconds * 1000)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (out / 'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(timeline)) + '\n')
    # Intermediate speech files are not included in Actions artifacts.
    for path in [*raw_paths, *out.glob('scene-*.wav')]:
        path.unlink()
    return timeline
