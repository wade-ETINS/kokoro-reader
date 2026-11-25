"""Translate an SRT line by line with local Opus-MT (ctranslate2), keeping every timing.

Usage:  .venv\\Scripts\\python.exe translate_srt.py <in.srt> --to zh|en [--out out.srt]
English -> Chinese output is converted to Traditional characters with Taiwan wording (OpenCC s2twp).
"""
import argparse
import re
import time
from pathlib import Path

import ctranslate2
import opencc
from transformers import MarianTokenizer

MODELS = Path(__file__).resolve().parent / "models"


def read_srt(path):
    blocks = re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig").strip())
    cues = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 3 and "-->" in lines[1]:
            cues.append((lines[1].strip(), " ".join(l.strip() for l in lines[2:])))
    return cues


class Translator:
    def __init__(self, to):
        pair = "en-zh" if to == "zh" else "zh-en"
        d = MODELS / f"opus-mt-{pair}"
        self.tok = MarianTokenizer.from_pretrained(str(d))
        self.tr = ctranslate2.Translator(str(d), device="cpu", compute_type="int8")
        self.prefix = ">>cmn_Hant<< " if to == "zh" else ""
        self.cc = opencc.OpenCC("s2twp") if to == "zh" else None

    def __call__(self, texts, batch=16, glossary=None):
        glossary = sorted((glossary or {}).items(), key=lambda kv: -len(kv[0]))
        slots = []
        protected = []
        for t in texts:
            found = {}
            for k, (term, target) in enumerate(glossary):
                pat = re.compile(re.escape(term), re.I)
                if pat.search(t):
                    tag = f"X{k}Q"
                    t = pat.sub(tag, t)
                    found[tag] = target
            slots.append(found)
            protected.append(t)
        texts = protected
        src = [self.tok.convert_ids_to_tokens(self.tok.encode(self.prefix + t)) for t in texts]
        res = self.tr.translate_batch(src, max_batch_size=batch, beam_size=4)
        out = [self.tok.decode(self.tok.convert_tokens_to_ids(r.hypotheses[0]), skip_special_tokens=True)
               for r in res]
        if self.cc:
            out = [self.cc.convert(o) for o in out]
        fixed = []
        for o, found in zip(out, slots):
            for tag, target in found.items():
                pat = (r"\s*" + re.escape(tag) + r"\s*") if re.search(CJK, target) else re.escape(tag)
                o = re.sub(pat, lambda _m, s=target: s, o, flags=re.I)
            if self.cc:
                o = tidy_zh(o)
            fixed.append(o)
        return fixed


CJK = r"[㐀-鿿＀-￯]"


def tidy_zh(s):
    s = re.sub(rf"\s+([，。、！？：；])", r"\1", s)
    s = s.replace(",", "，").replace("?", "？").replace("!", "！").replace(":", "：").replace(";", "；")
    s = re.sub(rf"(?<={CJK})\s+(?={CJK})", "，", s)          # model uses spaces as commas
    s = re.sub(rf"(?<={CJK})\s+(?=[A-Za-z0-9])|(?<=[A-Za-z0-9])\s+(?={CJK})", " ", s)
    s = re.sub(r"，{2,}", "，", s)
    s = re.sub(r"，([。！？])", r"\1", s)
    return s.strip(" ，")


def load_glossary(path):
    """Lines 'source = target'; 'term' alone means keep it as is. # starts a comment."""
    g = {}
    if path and Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                src, _, dst = line.partition("=")
                g[src.strip()] = (dst.strip() or src.strip())
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("srt")
    ap.add_argument("--to", choices=["zh", "en", "auto"], default="auto",
                    help="auto: Chinese subtitles -> English, anything else -> Chinese")
    ap.add_argument("--out")
    ap.add_argument("--glossary", default=str(Path(__file__).resolve().parent / "glossary.txt"))
    a = ap.parse_args()
    src = Path(a.srt)
    if a.to == "auto":
        body = " ".join(t for _, t in read_srt(src))
        a.to = "en" if len(re.findall(CJK, body)) > 0.2 * max(1, len(body.replace(" ", ""))) else "zh"
        print("translate to", "English" if a.to == "en" else "Chinese (Taiwan)")
    out = Path(a.out) if a.out else src.with_name(f"{src.stem}.{'zh-TW' if a.to == 'zh' else 'en'}.srt")
    cues = read_srt(src)
    t0 = time.time()
    tr = Translator(a.to)
    load = time.time() - t0
    t1 = time.time()
    texts = tr([t for _, t in cues], glossary=load_glossary(a.glossary))
    took = time.time() - t1
    with open(out, "w", encoding="utf-8") as f:
        for n, ((tm, _), t) in enumerate(zip(cues, texts), 1):
            f.write(f"{n}\n{tm}\n{t}\n\n")
    print(f"{len(cues)} lines -> {out}  (load {load:.1f}s, translate {took:.1f}s)")


if __name__ == "__main__":
    main()
