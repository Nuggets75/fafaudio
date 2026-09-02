"""
Generate a XACT2 .xap project file (August 2007 SDK, Content Version 43).

The Global Settings block (categories, variables, RPC presets, compression
presets) is taken verbatim from the official Supreme Commander XACT template
published at gitlab.com/supreme-commander-forged-alliance/other/audio, so
categories match what the game engine expects.

Per-sound settings supported: category, volume, pitch, priority, loop count,
volume variation, pitch variation.
"""

import os
from typing import List, Dict

_HERE = os.path.dirname(os.path.abspath(__file__))
_GLOBAL_SETTINGS_PATH = os.path.join(_HERE, "templates_xact", "global_settings.txt")

with open(_GLOBAL_SETTINGS_PATH, "r", encoding="utf-8") as _fh:
    GLOBAL_SETTINGS_TEMPLATE = _fh.read()

# Categories available in the FA template, in tree order.
CATEGORIES = [
    "Default", "Music", "World", "Units", "Ambient", "Weapons", "Destroy",
    "Rumble", "Interface", "UnitsUEF", "UnitsAEON", "UnitsCYBRAN",
    "UnitsUEFAir", "UnitsCYBRANAir", "UnitsAEONAir", "ActiveLoopsUEF",
    "ActiveLoopsCYBRAN", "ActiveLoopsAEON", "UnitSelect", "FMV",
    "Op_Briefing", "VO", "US", "DE", "ES", "FR", "IT", "RU", "PL", "CN",
    "CZ", "KR", "Construction_Loops", "UnitsSeraphimAir", "UnitsSeraphim",
    "ActiveLoopsSeraphim", "ConstructionSeraphim", "SeraphimSea",
]

# Compression presets defined in the FA template ("<none>" = uncompressed PCM).
COMPRESSION_PRESETS = ["<none>", "ADPCM 128", "ADPCM 256", "ADPCM 512"]


WAVE_BANK_HEADER = """
Wave Bank
{
    Name = %(bank)s;
    Xbox File = Xbox\\%(bank)s.xwb;
    Windows File = Win\\%(bank)s.xwb;
    Xbox Bank Path Edited = 0;
    Windows Bank Path Edited = 0;
    Seek Tables = 1;
    Compression Preset Name = %(preset)s;
    Xbox Bank Last Modified Low = 0;
    Xbox Bank Last Modified High = 0;
    PC Bank Last Modified Low = 0;
    PC Bank Last Modified High = 0;
    Header Last Modified Low = 0;
    Header Last Modified High = 0;
    Bank Last Revised Low = 0;
    Bank Last Revised High = 0;
%(streaming)s"""

WAVE_ENTRY_TEMPLATE = """
    Wave
    {
        Name = %(cue)s;
        File = %(filename)s;
        Build Settings Last Modified Low = 0;
        Build Settings Last Modified High = 0;

        Cache
        {
            Format Tag = 0;
            Channels = %(channels)d;
            Sampling Rate = %(rate)d;
            Bits Per Sample = 1;
            Play Region Offset = 44;
            Play Region Length = %(data_length)d;
            Loop Region Offset = 0;
            Loop Region Length = 0;
            File Type = 1;
            Last Modified Low = 0;
            Last Modified High = 0;
        }
    }
"""

WAVE_BANK_FOOTER = "}\n"

SOUND_BANK_HEADER = """
Sound Bank
{
    Name = %(bank)s;
    Xbox File = Xbox\\%(bank)s.xsb;
    Windows File = Win\\%(bank)s.xsb;
    Xbox Bank Path Edited = 0;
    Windows Bank Path Edited = 0;
    Bank Last Modified Low = 0;
    Bank Last Modified High = 0;
    Header Last Modified High = 0;
    Header Last Modified Low = 0;
"""

SOUND_BANK_FOOTER = "}\n"


def _sound_block(s: Dict, bank_name: str, index: int) -> str:
    """Render one Sound block with its per-file settings."""
    cue = s["cue"]
    lines = []
    lines.append("\n    Sound\n    {")
    lines.append("        Name = %s;" % cue)
    lines.append("        Volume = %d;" % s.get("volume_mb", 0))
    lines.append("        Pitch = %d;" % s.get("pitch", 0))
    lines.append("        Priority = %d;" % s.get("priority", 0))
    lines.append("")
    lines.append("        Category Entry\n        {")
    lines.append("            Name = %s;" % s.get("category", "Default"))
    lines.append("        }")
    lines.append("")
    lines.append("        Track\n        {")
    lines.append("            Volume = 0;")
    lines.append("")
    lines.append("            Play Wave Event\n            {")

    # Loop Count comes first inside Play Wave Event when present.
    loop_count = s.get("loop_count", 0)
    if loop_count and loop_count > 0:
        lines.append("                Loop Count = %d;" % loop_count)

    lines.append("                Break Loop = 0;")
    lines.append("                Use Speaker Position = 0;")
    lines.append("                Use Center Speaker = 1;")
    lines.append("                New Speaker Position On Loop = 1;")
    lines.append("                Speaker Position Angle = 0.000000;")
    # NOTE: "Speaer" typo is present in the real XACT format; keep it.
    lines.append("                Speaer Position Arc = 0.000000;")
    lines.append("")
    lines.append("                Event Header\n                {")
    lines.append("                    Timestamp = 0;")
    lines.append("                    Relative = 0;")
    lines.append("                    Random Recurrence = 0;")
    lines.append("                    Random Offset = 0;")
    lines.append("                }")

    # Pitch variation (semitones * 100 -> XACT units)
    if s.get("pitch_var_enabled"):
        lines.append("")
        lines.append("                Pitch Variation\n                {")
        lines.append("                    Min = %d;" % s.get("pitch_var_min", -100))
        lines.append("                    Max = %d;" % s.get("pitch_var_max", 100))
        lines.append("                    Operator = 0;")
        lines.append("                    New Variation On Loop = 0;")
        lines.append("                }")

    # Volume variation (dB * 100 -> millibels)
    if s.get("vol_var_enabled"):
        lines.append("")
        lines.append("                Volume Variation\n                {")
        lines.append("                    Min = %d;" % s.get("vol_var_min", -200))
        lines.append("                    Max = %d;" % s.get("vol_var_max", 0))
        lines.append("                    Volume = 0;")
        lines.append("                    New Variation On Loop = 0;")
        lines.append("                }")

    lines.append("")
    lines.append("                Variation\n                {")
    lines.append("                    Variation Type = 3;")
    lines.append("                    Variation Table Type = 0;")
    lines.append("                    New Variation on Loop = 0;")
    lines.append("                }")
    lines.append("")
    lines.append("                Wave Entry\n                {")
    lines.append("                    Bank Name = %s;" % bank_name)
    lines.append("                    Bank Index = 0;")
    lines.append("                    Entry Name = %s;" % cue)
    lines.append("                    Entry Index = %d;" % index)
    lines.append("                    Weight = 255;")
    lines.append("                    Weight Min = 0;")
    lines.append("                }")
    lines.append("            }")
    lines.append("        }")
    lines.append("    }")
    return "\n".join(lines) + "\n"


def _cue_block(cue: str, index: int) -> str:
    return (
        "\n    Cue\n    {\n"
        "        Name = %s;\n"
        "\n"
        "        Variation\n        {\n"
        "            Variation Type = 3;\n"
        "            Variation Table Type = 1;\n"
        "            New Variation on Loop = 0;\n"
        "        }\n"
        "\n"
        "        Sound Entry\n        {\n"
        "            Name = %s;\n"
        "            Index = %d;\n"
        "            Weight Min = 0;\n"
        "            Weight Max = 255;\n"
        "        }\n"
        "    }\n" % (cue, cue, index)
    )


def generate_xap(bank_name: str, waves: List[Dict],
                 compression_preset: str = "<none>",
                 streaming: bool = False) -> str:
    """
    Build a full .xap project.

    waves entries support these keys:
        filename, cue, channels, rate, data_length   (required, set by server)
        category          str, default "Default"
        volume_mb         int millibels, default 0
        pitch             int (semitones * 100), default 0
        priority          int 0-255, default 0
        loop_count        int, 0 = no loop, 255 = infinite
        vol_var_enabled   bool
        vol_var_min/max   int millibels
        pitch_var_enabled bool
        pitch_var_min/max int (semitones * 100)
    """
    if compression_preset not in COMPRESSION_PRESETS:
        compression_preset = "<none>"

    parts = []
    parts.append(GLOBAL_SETTINGS_TEMPLATE % {"bank": bank_name})

    parts.append(WAVE_BANK_HEADER % {
        "bank": bank_name,
        "preset": compression_preset,
        "streaming": "    Streaming = 1;\n" if streaming else "",
    })
    for w in waves:
        parts.append(WAVE_ENTRY_TEMPLATE % {
            "cue": w["cue"],
            "filename": w["filename"],
            "channels": w.get("channels", 2),
            "rate": w.get("rate", 48000),
            "data_length": w.get("data_length", 0),
        })
    parts.append(WAVE_BANK_FOOTER)

    parts.append(SOUND_BANK_HEADER % {"bank": bank_name})
    for idx, w in enumerate(waves):
        parts.append(_sound_block(w, bank_name, idx))
    for idx, w in enumerate(waves):
        parts.append(_cue_block(w["cue"], idx))
    parts.append(SOUND_BANK_FOOTER)

    return "".join(parts)
