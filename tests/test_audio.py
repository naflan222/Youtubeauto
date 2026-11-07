import json
import math
from pathlib import Path
import struct
import subprocess
import wave
from unittest.mock import Mock
import pytest
from shorts import audio


def measurement(peak=-3, loudness=-17):
    return {'input_i': str(loudness), 'input_tp': str(peak), 'input_lra': '4', 'input_thresh': '-27', 'target_offset': '0'}


def test_peak_overshoot_is_corrected_from_original_wav(monkeypatch, tmp_path):
    source = tmp_path / 'source.wav'
    source.touch()
    monkeypatch.setattr(audio, 'measure_loudness', Mock(side_effect=[measurement(), measurement(peak=0.6), measurement(peak=-2.6)]))
    commands = []
    def encode(command, **kwargs):
        commands.append(command)
        Path(command[-1]).write_bytes(b'encoded AAC')
    monkeypatch.setattr(audio.subprocess, 'run', encode)
    result = audio.encode_narration(source, tmp_path)
    assert result.read_bytes() == b'encoded AAC'
    assert len(commands) == 2
    assert all(command[command.index('-i')+1] == str(source) for command in commands)
    assert 'volume=-3.100dB' in commands[1][commands[1].index('-af')+1]
    assert not (tmp_path / 'audio-candidate.m4a').exists()
    report = json.loads((tmp_path / 'audio-normalization.json').read_text())
    assert report['encoded_checks'][-1]['true_peak_db'] <= audio.TARGET_PEAK_DB


def test_persistent_unsafe_peak_fails_after_bounded_attempts(monkeypatch, tmp_path):
    monkeypatch.setattr(audio, 'measure_loudness', Mock(return_value=measurement(peak=0)))
    encode = Mock()
    monkeypatch.setattr(audio.subprocess, 'run', encode)
    with pytest.raises(ValueError, match='peak remains unsafe'):
        audio.encode_narration(tmp_path / 'input.wav', tmp_path)
    assert encode.call_count == 3
    assert not (tmp_path / 'narration.m4a').exists()


def test_too_quiet_audio_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(audio, 'measure_loudness', Mock(side_effect=[measurement(), measurement(loudness=-45)]))
    monkeypatch.setattr(audio.subprocess, 'run', Mock())
    with pytest.raises(ValueError, match='too quiet'):
        audio.encode_narration(tmp_path / 'input.wav', tmp_path)


def test_real_aac_encoding_resampling_and_remux_keep_safe_peaks(tmp_path):
    # Speech-like bursts plus high-frequency transients exercise 22.05 -> 48 kHz
    # resampling and lossy-encoder overshoot rather than a mocked filter string.
    rate = 22050
    source = tmp_path / 'source.wav'
    samples = bytearray()
    for i in range(rate * 5):
        t = i / rate
        envelope = 1 if t % 0.7 < 0.55 else .05
        value = envelope * (.73 * math.sin(2*math.pi*440*t) + .23 * math.sin(2*math.pi*8500*t))
        samples.extend(struct.pack('<h', round(value * 32767)))
    with wave.open(str(source), 'wb') as wav:
        wav.setparams((1,2,rate,0,'NONE','not compressed'))
        wav.writeframes(samples)
    encoded = audio.encode_narration(source, tmp_path)
    assert float(audio.measure_loudness(encoded)['input_tp']) <= audio.TARGET_PEAK_DB
    # The renderer uses this identical stream-copy operation for the MP4.
    remux = tmp_path / 'remux.mp4'
    subprocess.run(['ffmpeg','-v','error','-i',str(encoded),'-c:a','copy',str(remux)],check=True)
    probe = json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-of','json',str(remux)],capture_output=True,text=True,check=True).stdout)['streams'][0]
    assert probe['codec_name'] == 'aac' and probe['sample_rate'] == '48000'
    assert abs(float(probe['duration']) - 5) < .05
    assert float(audio.measure_loudness(remux)['input_tp']) <= audio.TARGET_PEAK_DB
    hashes = []
    for path in [encoded, remux]:
        hashes.append(subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-'],capture_output=True,text=True,check=True).stdout)
    assert hashes[0] == hashes[1]
