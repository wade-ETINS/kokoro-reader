# Credits

Kokoro Reader is built on the work of these projects. Thank you to their authors.
None of their files are stored in this repository: the build scripts download them.

## Models

| What | By | Licence | Used for |
|---|---|---|---|
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | hexgrad | Apache-2.0 | English voices |
| [Kokoro-82M-v1.1-zh](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh) | hexgrad | Apache-2.0 | Chinese voices |
| Whisper large-v3-turbo and small | OpenAI | MIT | Speech recognition (step 1) |
| [faster-whisper-large-v3-turbo](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo) | Mobius Labs | MIT | CTranslate2 conversion of Whisper turbo |
| [faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small) | SYSTRAN | MIT | CTranslate2 conversion of Whisper small |
| [opus-mt-en-zh](https://huggingface.co/Helsinki-NLP/opus-mt-en-zh), [opus-mt-zh-en](https://huggingface.co/Helsinki-NLP/opus-mt-zh-en) | Helsinki-NLP (University of Helsinki) | CC-BY-4.0 | Translation (step 2), converted to CTranslate2 int8 by `get_mt_models.py` |

Opus-MT: Jörg Tiedemann and Santhosh Thottingal, "OPUS-MT – Building open translation services for the World",
EAMT 2020.

## Software

| What | Licence | Used for |
|---|---|---|
| [kokoro](https://github.com/hexgrad/kokoro) and [misaki](https://github.com/hexgrad/misaki) 0.9.4 | Apache-2.0 | Kokoro inference and text-to-phoneme |
| [eSpeak NG](https://github.com/espeak-ng/espeak-ng) | GPL-3.0 | Phonemes for English fallback |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 1.2.1 | MIT | Whisper inference |
| [CTranslate2](https://github.com/OpenNMT/CTranslate2) 4.9 | MIT | Fast CPU inference for Whisper and Opus-MT |
| [Transformers](https://github.com/huggingface/transformers) | Apache-2.0 | Opus-MT tokenizer |
| [OpenCC](https://github.com/yichen0831/opencc-python) (opencc-python-reimplemented) | Apache-2.0 | Simplified → Traditional Chinese (Taiwan phrasing) |
| [jieba](https://github.com/fxsjy/jieba) | MIT | Chinese word boundaries when splitting lines |
| [PyTorch](https://pytorch.org) | BSD-3-Clause | Model runtime |
| [spaCy](https://spacy.io) | MIT | English text processing in misaki |
| [Flask](https://flask.palletsprojects.com) | BSD-3-Clause | Local web server for the UI |
| [FFmpeg](https://ffmpeg.org) | LGPL / GPL | Audio and video decoding and muxing |
| [FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) | LGPL build | FFmpeg for Windows |
| [Martin Riedl's FFmpeg builds](https://ffmpeg.martin-riedl.de) | GPL build | FFmpeg for macOS (Apple silicon) |
| [Python](https://www.python.org) 3.12 | PSF | Runtime (embeddable build on Windows) |
| [python-build-standalone](https://github.com/astral-sh/python-build-standalone) | see project | Python for macOS |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | Inno Setup licence | Windows installer |

The finished installers also contain a `licenses` folder with the licence files of every bundled Python package.
