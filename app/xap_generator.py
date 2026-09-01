"""
Generate a XACT2 .xap project file.

Format is that of the August 2007 DirectX SDK (Signature = XACT2, Version = 16),
which produces Content Version = 43 XWB files that FA/FAF accepts.

Template values (quoting, per-block field order, Variable definitions,
etc.) were taken from a known-working NameOrDeath.xap.
"""

from typing import List, Dict


HEADER = """Signature = XACT2;
Version = 16;
Content Version = 43;
Release = August 2007;

Options
{
    Verbose Report = 0;
    Generate C/C++ Headers = 1;
}

Global Settings
{
    Xbox File = Xbox\\%s.xgs;
    Windows File = Win\\%s.xgs;
    Header File = %s.h;
    Exclude Category Names = 0;
    Exclude Variable Names = 0;
    Last Modified Low = 0;
    Last Modified High = 0;

    Category
    {
        Name = Global;
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
        Name = Default;
        Public = 1;
        Background Music = 0;
        Volume = 0;

        Category Entry
        {
            Name = Global;
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
        Name = Music;
        Public = 1;
        Background Music = 1;
        Volume = 0;

        Category Entry
        {
            Name = Global;
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

    Variable
    {
        Name = OrientationAngle;
        Public = 1;
        Global = 0;
        Internal = 0;
        External = 0;
        Monitored = 1;
        Reserved = 1;
        Read Only = 0;
        Time = 0;
        Value = 0.000000;
        Initial Value = 0.000000;
        Min = -180.000000;
        Max = 180.000000;
    }

    Variable
    {
        Name = DopplerPitchScalar;
        Public = 1;
        Global = 0;
        Internal = 0;
        External = 0;
        Monitored = 1;
        Reserved = 1;
        Read Only = 0;
        Time = 0;
        Value = 1.000000;
        Initial Value = 1.000000;
        Min = 0.000000;
        Max = 4.000000;
    }

    Variable
    {
        Name = SpeedOfSound;
        Public = 1;
        Global = 1;
        Internal = 0;
        External = 0;
        Monitored = 1;
        Reserved = 1;
        Read Only = 0;
        Time = 0;
        Value = 343.500000;
        Initial Value = 343.500000;
        Min = 0.000000;
        Max = 1000000.000000;
    }

    Variable
    {
        Name = ReleaseTime;
        Public = 1;
        Global = 0;
        Internal = 1;
        External = 1;
        Monitored = 1;
        Reserved = 1;
        Read Only = 1;
        Time = 1;
        Value = 0.000000;
        Initial Value = 0.000000;
        Min = 0.000000;
        Max = 15.000001;
    }

    Variable
    {
        Name = AttackTime;
        Public = 1;
        Global = 0;
        Internal = 1;
        External = 1;
        Monitored = 1;
        Reserved = 1;
        Read Only = 1;
        Time = 1;
        Value = 0.000000;
        Initial Value = 0.000000;
        Min = 0.000000;
        Max = 15.000001;
    }

    Variable
    {
        Name = NumCueInstances;
        Public = 1;
        Global = 0;
        Internal = 1;
        External = 1;
        Monitored = 1;
        Reserved = 1;
        Read Only = 1;
        Time = 0;
        Value = 0.000000;
        Initial Value = 0.000000;
        Min = 0.000000;
        Max = 1024.000000;
    }

    Variable
    {
        Name = Distance;
        Public = 1;
        Global = 0;
        Internal = 0;
        External = 0;
        Monitored = 1;
        Reserved = 1;
        Read Only = 0;
        Time = 0;
        Value = 0.000000;
        Initial Value = 0.000000;
        Min = 0.000000;
        Max = 1000000.000000;
    }
}
"""

WAVE_BANK_HEADER = """
Wave Bank
{
    Name = %s;
    Xbox File = Xbox\\%s.xwb;
    Windows File = Win\\%s.xwb;
    Xbox Bank Path Edited = 0;
    Windows Bank Path Edited = 0;
    Seek Tables = 1;
    Compression Preset Name = <none>;
    Xbox Bank Last Modified Low = 0;
    Xbox Bank Last Modified High = 0;
    PC Bank Last Modified Low = 0;
    PC Bank Last Modified High = 0;
    Bank Last Revised Low = 0;
    Bank Last Revised High = 0;
"""

WAVE_ENTRY_TEMPLATE = """
    Wave
    {
        Name = %s;
        File = %s;
        Build Settings Last Modified Low = 0;
        Build Settings Last Modified High = 0;

        Cache
        {
            Format Tag = 0;
            Channels = %d;
            Sampling Rate = %d;
            Bits Per Sample = 1;
            Play Region Offset = 44;
            Play Region Length = %d;
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
    Name = %s;
    Xbox File = Xbox\\%s.xsb;
    Windows File = Win\\%s.xsb;
    Xbox Bank Path Edited = 0;
    Windows Bank Path Edited = 0;
    Bank Last Modified Low = 0;
    Bank Last Modified High = 0;
    Header Last Modified High = 0;
    Header Last Modified Low = 0;
"""

SOUND_ENTRY_TEMPLATE = """
    Sound
    {
        Name = %s;
        Volume = %d;
        Pitch = 0;
        Priority = 0;

        Category Entry
        {
            Name = Default;
        }

        Track
        {
            Volume = 0;

            Play Wave Event
            {
                Break Loop = 0;
                Use Speaker Position = 0;
                Use Center Speaker = 1;
                New Speaker Position On Loop = 1;
                Speaker Position Angle = 0.000000;
                Speaer Position Arc = 0.000000;

                Event Header
                {
                    Timestamp = 0;
                    Relative = 0;
                    Random Recurrence = 0;
                    Random Offset = 0;
                }

                Wave Entry
                {
                    Bank Name = %s;
                    Bank Index = 0;
                    Entry Name = %s;
                    Entry Index = %d;
                    Weight = 255;
                    Weight Min = 0;
                }
            }
        }
    }
"""

CUE_ENTRY_TEMPLATE = """
    Cue
    {
        Name = %s;

        Variation
        {
            Variation Type = 3;
            Variation Table Type = 1;
            New Variation on Loop = 0;
        }

        Sound Entry
        {
            Name = %s;
            Index = %d;
            Weight Min = 0;
            Weight Max = 255;
        }
    }
"""

SOUND_BANK_FOOTER = "}\n"


def generate_xap(bank_name: str, waves: List[Dict[str, str]],
                 volume_mb: int = 0) -> str:
    """
    Build a full .xap project text based on the August 2007 XACT2 format.

    Parameters
    ----------
    bank_name : identifier used for the Wave Bank and Sound Bank names,
                and as the output file prefix
    waves     : list of {"filename": "foo.wav", "cue": "foo",
                          "channels": int, "rate": int, "data_length": int}
    volume_mb : Volume in millibels applied to every Sound. 0 = as-recorded,
                positive = louder, negative = quieter. XACT range roughly
                -6000 to +1200.

    Returns the .xap content as a string.
    """
    parts = []
    parts.append(HEADER % (bank_name, bank_name, bank_name))

    parts.append(WAVE_BANK_HEADER % (bank_name, bank_name, bank_name))
    for w in waves:
        parts.append(WAVE_ENTRY_TEMPLATE % (
            w["cue"], w["filename"],
            w.get("channels", 2), w.get("rate", 48000), w.get("data_length", 0),
        ))
    parts.append(WAVE_BANK_FOOTER)

    parts.append(SOUND_BANK_HEADER % (bank_name, bank_name, bank_name))
    for idx, w in enumerate(waves):
        parts.append(
            SOUND_ENTRY_TEMPLATE % (w["cue"], volume_mb, bank_name, w["cue"], idx)
        )
    for idx, w in enumerate(waves):
        parts.append(CUE_ENTRY_TEMPLATE % (w["cue"], w["cue"], idx))
    parts.append(SOUND_BANK_FOOTER)

    return "".join(parts)
