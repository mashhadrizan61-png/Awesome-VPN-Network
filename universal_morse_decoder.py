#!/usr/bin/env python3
"""Universal Morse Decoder/Encoder with resilient decoding modes.

Features:
- Standard separated Morse decoding (supports spaces, /, | word separators)
- Auto-normalization for Unicode dashes and dots
- Fuzzy decoding for noisy signals (edit-distance nearest token)
- Continuous-stream decoding using beam-search segmentation
- Encoding plain text to Morse
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

MORSE_TABLE: Dict[str, str] = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "!": "-.-.--",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    "&": ".-...",
    ":": "---...",
    ";": "-.-.-.",
    "=": "-...-",
    "+": ".-.-.",
    "-": "-....-",
    "_": "..--.-",
    '"': ".-..-.",
    "$": "...-..-",
    "@": ".--.-.",
}

DECODE_TABLE = {v: k for k, v in MORSE_TABLE.items()}
MAX_TOKEN_LEN = max(len(token) for token in DECODE_TABLE)

COMMON_CHAR_PRIOR = {
    "E": 12.70,
    "T": 9.06,
    "A": 8.17,
    "O": 7.51,
    "I": 6.97,
    "N": 6.75,
    "S": 6.33,
    "H": 6.09,
    "R": 5.99,
    "D": 4.25,
    "L": 4.03,
    "U": 2.76,
}
DEFAULT_PRIOR = 1.2


@dataclass
class DecodeResult:
    text: str
    confidence: float
    mode: str
    alternatives: List[str]


def _normalize_symbols(data: str) -> str:
    replacements = {
        "·": ".",
        "•": ".",
        "—": "-",
        "–": "-",
        "−": "-",
        "_": "-",
        "|": " / ",
    }
    for old, new in replacements.items():
        data = data.replace(old, new)
    return " ".join(data.strip().split())


def _edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        prev = dp[0]
        dp[0] = i
        for j, cb in enumerate(b, start=1):
            old = dp[j]
            dp[j] = min(
                dp[j] + 1,
                dp[j - 1] + 1,
                prev + (0 if ca == cb else 1),
            )
            prev = old
    return dp[-1]


def _decode_token(token: str, fuzzy: bool = True) -> Tuple[str, float]:
    if token in DECODE_TABLE:
        return DECODE_TABLE[token], 1.0
    if not fuzzy:
        return "�", 0.0

    best_char = "�"
    best_dist = 10**9
    for known, ch in DECODE_TABLE.items():
        d = _edit_distance(token, known)
        if d < best_dist:
            best_char = ch
            best_dist = d
    conf = max(0.0, 1.0 - (best_dist / max(len(token), 1)))
    return best_char, conf


def decode_separated(message: str, fuzzy: bool = True) -> DecodeResult:
    message = _normalize_symbols(message)
    if not message:
        return DecodeResult("", 1.0, "separated", [])

    words: List[str] = []
    confidence_parts: List[float] = []

    for word_token in message.split(" /"):
        pieces = [p for p in word_token.strip().split(" ") if p]
        decoded = []
        for token in pieces:
            ch, conf = _decode_token(token, fuzzy=fuzzy)
            decoded.append(ch)
            confidence_parts.append(conf)
        words.append("".join(decoded))

    text = " ".join(filter(None, words)).strip()
    conf = sum(confidence_parts) / len(confidence_parts) if confidence_parts else 1.0
    return DecodeResult(text=text, confidence=round(conf, 4), mode="separated", alternatives=[])


def decode_continuous(signal: str, beam_width: int = 25, max_candidates: int = 5) -> DecodeResult:
    signal = _normalize_symbols(signal).replace(" ", "")
    if not signal:
        return DecodeResult("", 1.0, "continuous", [])
    if set(signal) - {".", "-"}:
        return DecodeResult("", 0.0, "continuous", [])

    beams: Dict[int, List[Tuple[float, str]]] = {0: [(0.0, "")]}
    for i in range(len(signal) + 1):
        if i not in beams:
            continue
        current = sorted(beams[i], key=lambda x: x[0], reverse=True)[:beam_width]
        for score, text in current:
            for ln in range(1, MAX_TOKEN_LEN + 1):
                j = i + ln
                if j > len(signal):
                    continue
                token = signal[i:j]
                ch = DECODE_TABLE.get(token)
                if not ch:
                    continue
                if ch.isdigit():
                    prior = 0.3
                elif ch.isalpha():
                    prior = COMMON_CHAR_PRIOR.get(ch, DEFAULT_PRIOR)
                else:
                    prior = 0.6
                new_score = score + math.log(prior) + (2.0 * ln) - 5.0
                beams.setdefault(j, []).append((new_score, text + ch))

    finals = sorted(beams.get(len(signal), []), key=lambda x: x[0], reverse=True)
    if not finals:
        return DecodeResult("", 0.0, "continuous", [])

    best_score = finals[0][0]
    best_text = finals[0][1]
    alternatives = [cand for _, cand in finals[1 : max_candidates + 1]]
    confidence = 1.0 if len(finals) == 1 else 1 / (1 + math.exp(finals[1][0] - best_score))
    return DecodeResult(
        text=best_text,
        confidence=round(confidence, 4),
        mode="continuous",
        alternatives=alternatives,
    )


def decode(message: str, mode: str = "auto", fuzzy: bool = True) -> DecodeResult:
    normalized = _normalize_symbols(message)
    if mode == "separated":
        return decode_separated(normalized, fuzzy=fuzzy)
    if mode == "continuous":
        return decode_continuous(normalized)

    if any(ch in normalized for ch in [" ", "/"]):
        return decode_separated(normalized, fuzzy=fuzzy)
    return decode_continuous(normalized)


def encode(text: str, word_sep: str = " / ") -> str:
    words = []
    for word in text.upper().split():
        encoded_chars = [MORSE_TABLE.get(ch, "?") for ch in word]
        words.append(" ".join(encoded_chars))
    return word_sep.join(words)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Universal Morse Decoder")
    parser.add_argument("message", nargs="?", default="", help="Morse text (or plain text in encode mode)")
    parser.add_argument("--mode", choices=["auto", "separated", "continuous", "encode"], default="auto")
    parser.add_argument("--no-fuzzy", action="store_true", help="Disable fuzzy decoding for noisy tokens")
    parser.add_argument("--json", action="store_true", help="Print full JSON output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.mode == "encode":
        output = encode(args.message)
        if args.json:
            print(json.dumps({"encoded": output}, ensure_ascii=False, indent=2))
        else:
            print(output)
        return 0

    result = decode(args.message, mode=args.mode, fuzzy=not args.no_fuzzy)
    if args.json:
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    else:
        print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
