# Asset and software rights

`LICENSES.json` records the installed pinned Python dependencies, their declared licenses, and asset sources. `voice.lock.json` records exact model URLs, a repository revision, and SHA-256 checksums. `requirements.lock` pins direct and transitive Python versions for Python 3.12/Linux. Ubuntu's FFmpeg/font packages follow the runner's security updates rather than a frozen OS image.

## Original content

The project author dedicates the original **Pip Bunny and Tilly Turtle character designs, procedural artwork, educational scripts, story text, and generated video/audio compositions** contributed by this project to the public domain under **CC0 1.0**: <https://creativecommons.org/publicdomain/zero/1.0/>. This permits copying, modification, commercial distribution, and YouTube publication. Educational source links are evidence references; source articles and their artwork are not copied into the videos.

The Python program source is **GPL-3.0-or-later**, matching its use of the GPL Piper library. See root `LICENSE`. Running the program to produce ordinary original graphics/narration does not by itself require distributing your output under the program's GPL license. Third-party assets retain their own licenses.

## Speech engine and model

- **Piper TTS 1.3.0:** GPL-3.0, <https://github.com/OHF-Voice/piper1-gpl>, [license](https://github.com/OHF-Voice/piper1-gpl/blob/main/COPYING). The packaged phonemizer uses eSpeak NG; preserve its license notices when redistributing engine binaries. This repository installs the upstream package and does not repackage its binaries.
- **Voice:** `en_US-ljspeech-medium` from <https://huggingface.co/rhasspy/piper-voices>. The repository [model metadata](https://huggingface.co/rhasspy/piper-voices/blob/e7229f7d33a10e145e109b886d661984201ac3c4/README.md) declares MIT. Its voice-specific [model card](https://huggingface.co/rhasspy/piper-voices/blob/e7229f7d33a10e145e109b886d661984201ac3c4/en/en_US/ljspeech/medium/MODEL_CARD) says it was trained from scratch on the **public-domain LJSpeech dataset**. [Dataset rights](https://keithito.com/LJ-Speech-Dataset/). These are distinct from Piper's engine license. The selected model has no stated noncommercial restriction in those checked declarations.
- The application downloads only the pinned voice, configuration, and model card. A changed checksum blocks operation. Preserve model provenance when redistributing it; do not assume all other Piper voices have the same rights.

## Fonts, rendering, and libraries

- **DejaVu Sans / Bold:** DejaVu/Bitstream Vera permissive font terms. [Full license](https://dejavu-fonts.github.io/License.html). Ubuntu package notices live under `/usr/share/doc/fonts-dejavu-core/`; embedded text rendering is permitted.
- **Pillow:** MIT-CMU (historically HPND/PIL permissive terms); see the installed package license files.
- **FFmpeg:** LGPL/GPL depending on build options. The Ubuntu build with `libx264` includes GPL components. [FFmpeg legal information](https://ffmpeg.org/legal.html). This project calls the installed executable and does not bundle it; video output is not made GPL merely by encoding it.
- **ONNX Runtime:** MIT; local CPU inference.
- **Google API Python client, Google authentication libraries:** Apache-2.0; used for the official API/OAuth flows.
- Full transitive package declarations, including test libraries, appear in `LICENSES.json`; retain upstream distribution notices if you redistribute dependency wheels. Metadata declarations supplement rather than replace those license texts.
- **Background music, stock footage, downloaded cartoons, social-media clips:** none used.

When adding fonts, voice models, sounds, images, or dependencies, verify the exact artifact's terms permit your use and update the manifest. Do not infer permission from the fact that a file can be downloaded.
