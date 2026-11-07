# Observed implementation verification

Verified on **2026-11-07**. Rendering, uploads, and account setup are separate claims: **no YouTube upload was attempted**, because Google credentials and an expected channel have not been supplied.

## Source and actual workflow runs

The tested implementation is commit **`c86d1d5fb25307a0cdc379d6ade19e191736cace`**. Subsequent documentation commits only add these verification links.

| Verification | Observed result |
| --- | --- |
| [Preview and tests](https://github.com/naflan222/Youtubeauto/actions/runs/42343665314) | Success; tests, full render, validation, artifact upload |
| [Daily original Short, manually dispatched in preview mode](https://github.com/naflan222/Youtubeauto/actions/runs/42343665116) | Success; actual daily/manual workflow path; no credentials used and no upload |
| Local Python 3.12 test suite | **58 passed** |
| GitHub Python 3.12 test suite, in each workflow | **57 passed, 1 skipped**, followed by the full preview CLI render and media validation |
| Editable project installation | Successful with the pinned build tools and `--no-deps --no-build-isolation` |
| Dependency compatibility | `pip check`: no broken requirements |
| Syntax | `compileall` passed for application and setup tools |

The skipped test on GitHub checks an already-rendered local video; none exists before its rendering step. Each workflow's later CLI step performs the actual complete ffprobe/audio/layout validation, so the skip does not replace media verification.

The first daily preview exposed an AAC peak issue, correctly preventing publication. The final implementation uses measured two-pass loudness normalization and a limiter. Both workflow links above are successful reruns of the corrected source.

## Downloadable sample

[Download the successful preview workflow artifact ZIP](https://github.com/naflan222/Youtubeauto/actions/runs/42343665314/artifacts/13562124110). It contains the full MP4, captions, metadata, representative frames, and validation report. GitHub sign-in may be required. **Artifacts expire after three days**; rerun the preview workflow to generate another downloadable video.

Small permanent sample records:

- [Script and metadata](../examples/sample/script.json)
- [Readable script](../examples/sample/script.txt)
- [Captions](../examples/sample/captions.srt)
- [Measured media validation](../examples/sample/validation.json)
- [Independent speech check](../examples/sample/speech-verification.json)

A complete local copy is also provided in the task workspace under `library-files/youtubeauto-preview/preview.mp4`. The available GitHub credential was rejected by the release-attachment endpoint, so no release download is claimed. The failed release creation left no release behind.

The local sample was rendered by the same tested implementation. Each workflow independently rendered and validated its own sample. Piper synthesis has stochastic variation, so waveform hashes need not match between runs.

Local sample results:

| Property | Observed |
| --- | --- |
| Title | Which Group Has More Flowers? |
| Duration | 31.9 seconds |
| Frame | 1080 × 1920, 30 fps |
| Video / audio | H.264/yuv420p / AAC |
| Mean / peak decoded audio | −17.3 dB / −1.3 dB (ffmpeg volumedetect, not integrated LUFS) |
| Black or long silent gaps | None detected by the configured checks |
| Captions | Five measured scene intervals; mobile layout checks passed |
| Audience metadata | `selfDeclaredMadeForKids=true` |
| Selection | `evergreen-fallback` |
| Video SHA-256 | `57905c82fd97d5fd59800facb1e6b0260d81b73596a64a7e01d9ba20222160e4` |

Representative scene frames and the final frame were visually inspected. Character/text overlap discovered during implementation was corrected. All 40 episodes' caption and graphic layouts are exercised by tests.

An independent **offline faster-whisper tiny.en** transcription of the final sample produced **96.36% normalized word-sequence similarity** to the script. Most differences involved Pip's name. This is an automated intelligibility check, **not a human listening assessment** or a guarantee of perfect pronunciation. The verification-only environment used faster-whisper 1.2.1 and PyAV 16.0.1; neither ASR package nor its model is required by the daily pipeline.

## Still account-dependent

The OAuth browser consent flow, actual authenticated channel identity, live discovery responses, resumable upload acceptance, YouTube processing, and public publication require the owner's Google/YouTube account. Their code paths have recovery tests, but those tests are not a claim of a live upload. Follow [SETUP.md](SETUP.md) for the exact one-time steps, then perform the first enabled manual publication.
