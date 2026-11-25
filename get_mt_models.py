"""Download Opus-MT en->zh and zh->en and convert them for ctranslate2 into models/ (int8)."""
from pathlib import Path

import truststore

truststore.inject_into_ssl()
from ctranslate2.converters import TransformersConverter  # noqa: E402

ROOT = Path(__file__).resolve().parent / "models"
for pair in ("en-zh", "zh-en"):
    out = ROOT / f"opus-mt-{pair}"
    if (out / "model.bin").exists():
        print(out, "already there")
        continue
    TransformersConverter(f"Helsinki-NLP/opus-mt-{pair}",
                          copy_files=["source.spm", "target.spm", "vocab.json", "tokenizer_config.json"]
                          ).convert(str(out), quantization="int8", force=True)
    print(out, sum(f.stat().st_size for f in out.iterdir()) // 2**20, "MB")
