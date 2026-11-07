"""Normalize and check the actual encoded narration before video rendering."""
import json
import math
import subprocess

TARGET_PEAK_DB = -2.0


def measure_loudness(path):
    scan = subprocess.run(
        ['ffmpeg', '-hide_banner', '-i', str(path), '-vn', '-af',
         'loudnorm=I=-16:TP=-4:LRA=7:print_format=json', '-f', 'null', '-'],
        capture_output=True, text=True, check=True,
    ).stderr
    measurement = json.loads(scan[scan.rfind('{'):scan.rfind('}') + 1])
    if not all(math.isfinite(float(measurement[key])) for key in
               ['input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset']):
        raise ValueError('Narration has no measurable finite loudness; publication skipped')
    return measurement


def encode_narration(source, out):
    """Check AAC decoding too: filters alone cannot guarantee encoder peak level.

    Each attempt starts from the original WAV, avoiding repeated lossy encoding.
    The accepted AAC is copied into the MP4 without another encoding step.
    """
    source_measurement = measure_loudness(source)
    report = dict(source_measurement)
    report.update(target_encoded_true_peak_db=TARGET_PEAK_DB, encoded_checks=[])
    report_path = out / 'audio-normalization.json'
    normalization = (
        'loudnorm=I=-16:TP=-4:LRA=7:linear=true'
        + ':measured_I=' + source_measurement['input_i']
        + ':measured_TP=' + source_measurement['input_tp']
        + ':measured_LRA=' + source_measurement['input_lra']
        + ':measured_thresh=' + source_measurement['input_thresh']
        + ':offset=' + source_measurement['target_offset']
        # Resample BEFORE limiting, and compensate the limiter look-ahead.
        + ',aresample=48000,alimiter=limit=0.630957:level=false:latency=true'
    )
    candidate = out / 'audio-candidate.m4a'
    final = out / 'narration.m4a'
    correction_db = 0.0
    for attempt in range(3):
        subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-af',
             normalization + f',volume={correction_db:.3f}dB',
             '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '1', str(candidate)],
            check=True,
        )
        decoded = measure_loudness(candidate)
        peak = float(decoded['input_tp'])
        loudness = float(decoded['input_i'])
        report['encoded_checks'].append({
            'attempt': attempt + 1, 'correction_db': correction_db,
            'true_peak_db': peak, 'integrated_lufs': loudness,
        })
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        if loudness < -30:
            candidate.unlink(missing_ok=True)
            raise ValueError('Encoded narration too quiet; publication skipped')
        if peak <= TARGET_PEAK_DB:
            candidate.replace(final)
            return final
        # Aim below the boundary to allow for codec rounding on the next attempt.
        correction_db += TARGET_PEAK_DB - 0.5 - peak
    candidate.unlink(missing_ok=True)
    raise ValueError('Encoded narration peak remains unsafe; publication skipped')
