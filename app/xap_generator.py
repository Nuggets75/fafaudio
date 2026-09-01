"""
Generate a minimal XACT .xap project file from a list of wave entries.

The format is that of the DirectX SDK XACT tool (2008-era, "Content Version = 43").
This is what FA/FAF's audio engine accepts. XACT tools from later SDKs
(June 2010 onwards) produce Content Version 46 which FA rejects.

References for field values:
- Standard XACT project templates from the DirectX SDK samples
- Working .xap projects from the FAF modding community

If the CLI builder rejects an output from this generator, the fix is
usually a missing property block, not a wrong value in an existing one.
"""

from typing import List, Dict


HEADER = """Signature = XACT3;
Version = 18;
Content Version = 43;
Release = March 2008;

Options
{
    Verbose Report = 0;
    Generate C/C++ Headers = 1;
}

Global Settings
{
    Xbox File = "Xbox\\GlobalSettings.xgs";
    Windows File = "Win\\GlobalSettings.xgs";
    Header File = "GlobalSettings.h";
    Exclude Category Names = 0;
    Exclude Variable Names = 0;
    Last Modified Low = 0;
    Last Modified High = 0;

    Category
    {
        Name = "Global";
        Public = 1;
        Background Music = 0;
        Volume = 0;
        Category Entry
        {
        }

        Instance Limit
        {
            Max Instances = 255;
            Behavior = 0;

            Crossfade
            {
                Fade In = 0;
                Fade Out = 0;
                Crossfade Type = 0;
            }
        }
    }

    Category
    {
        Name = "Default";
        Public = 1;
        Background Music = 0;
        Volume = 0;
        Category Entry
        {
            Name = "Global";
        }

        Instance Limit
        {
            Max Instances = 255;
            Behavior = 0;

            Crossfade
            {
                Fade In = 0;
                Fade Out = 0;
                Crossfade Type = 0;
            }
        }
    }

    Category
    {
        Name = "Music";
        Public = 1;
        Background Music = 1;
        Volume = 0;
        Category Entry
        {
            Name = "Global";
        }

        Instance Limit
        {
            Max Instances = 255;
            Behavior = 0;

            Crossfade
            {
                Fade In = 0;
                Fade Out = 0;
                Crossfade Type = 0;
            }
        }
    }

    File Notification Interval Ms = 250;

    RS
    {
        Name = "InGame";
        Public = 1;
        RS Curve Def
        {
            Segment
            {
                Point0 = 0.000000, 0.000000, 0;
                Point1 = 1.000000, 1.000000, 0;
            }
        }
    }
}
"""

WAVE_BANK_HEADER = """
Wave Bank
{{
    Name = "{bank_name}";
    Xbox File = "Xbox\\{bank_name}.xwb";
    Windows File = "Win\\{bank_name}.xwb";
    Xbox Bank Path Edited = 0;
    Windows Bank Path Edited = 0;
    Header File = "{bank_name}.h";
    Bank Last Revised Low = 0;
    Bank Last Revised High = 0;
    Bank Release = 0;

    Streaming = 0;
    Seek Tables = 0;
    Compression Preset Name = "<none>";
    Include Names = 1;

    Last Modified Low = 0;
    Last Modified High = 0;
"""

WAVE_ENTRY = """
    Wave
    {{
        Name = "{cue}";
        File = "{filename}";
        Build Settings Last Modified Low = 0;
        Build Settings Last Modified High = 0;

        Cache
        {{
            Format Tag = 0;
            Channels = 1;
            Sampling Rate = 44100;
            Bits Per Sample = 1;
            Play Region Offset = 0;
            Play Region Length = 0;
            Loop Region Offset = 0;
            Loop Region Length = 0;
            File Type = 1;
            Last Modified Low = 0;
            Last Modified High = 0;
        }}
    }}
"""

WAVE_BANK_FOOTER = "}\n"

SOUND_BANK_HEADER = """
Sound Bank
{{
    Name = "{bank_name}";
    Xbox File = "Xbox\\{bank_name}.xsb";
    Windows File = "Win\\{bank_name}.xsb";
    Xbox Bank Path Edited = 0;
    Windows Bank Path Edited = 0;
    Header File = "{bank_name}.h";
    Exclude Category Names = 0;
    Exclude Variable Names = 0;

    Last Modified Low = 0;
    Last Modified High = 0;
"""

SOUND_ENTRY = """
    Sound
    {{
        Name = "{cue}";
        Volume = -600;
        Pitch = 0;
        Priority = 0;

        Category Entry
        {{
            Name = "Default";
        }}

        Track
        {{
            Volume = 0;
            Use Filter = 0;

            Play Wave Event
            {{
                Break Loop = 0;
                Use Speaker Position = 0;
                Use Center Speaker = 1;
                New Speaker Position On Loop = 1;
                Speaker Position Angle = 0.000000;
                Speaker Position Arc = 0.000000;

                Event Header
                {{
                    Timestamp = 0;
                    Relative = 0;
                    Random Recurrence = 0;
                    Random Offset = 0;
                }}

                Wave Entry
                {{
                    Bank Name = "{bank_name}";
                    Bank Index = 0;
                    Entry Name = "{cue}";
                    Entry Index = {index};
                    Weight = 255;
                    Weight Min = 0;
                }}
            }}
        }}
    }}
"""

CUE_ENTRY = """
    Cue
    {{
        Name = "{cue}";
        Sound Entry
        {{
            Name = "{cue}";
            Index = {index};
            Weight Min = 0;
            Weight Max = 255;
        }}
        Variation
        {{
            Variation Type = 3;
            Variation Table Type = 1;
            New Variation On Loop = 0;
        }}
    }}
"""

SOUND_BANK_FOOTER = "}\n"


def generate_xap(bank_name: str, waves: List[Dict[str, str]]) -> str:
    """
    Build a full .xap project text.

    Parameters
    ----------
    bank_name : bank identifier (used for Wave Bank AND Sound Bank names,
                and as the output filename prefix)
    waves     : list of {"filename": "foo.wav", "cue": "foo"} dicts

    Returns the .xap content as a string.
    """
    parts = [HEADER]

    parts.append(WAVE_BANK_HEADER.format(bank_name=bank_name))
    for w in waves:
        parts.append(
            WAVE_ENTRY.format(cue=w["cue"], filename=w["filename"])
        )
    parts.append(WAVE_BANK_FOOTER)

    parts.append(SOUND_BANK_HEADER.format(bank_name=bank_name))
    for idx, w in enumerate(waves):
        parts.append(
            SOUND_ENTRY.format(
                cue=w["cue"], bank_name=bank_name, index=idx
            )
        )
    for idx, w in enumerate(waves):
        parts.append(CUE_ENTRY.format(cue=w["cue"], index=idx))
    parts.append(SOUND_BANK_FOOTER)

    return "".join(parts)
