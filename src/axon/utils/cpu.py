
from __future__ import annotations
import platform
import re
import subprocess
import sys
from pathlib import Path

class CPUInfo:
    """
    CPUInfo 的 Docstring
    Methods:
        name:return the normalized CPU name using paltform-specific sources with robust fallbacks.
        _clear: normalize and prettify common vendor brand strings and frequency patterns.
        __str__:return the normalized CPU name for string contexts.
    Examples:
        >>>CPUInfo.name()
        'Apple M4'
        >>>str(CPUInfo())
        'Apple M4'
    """

    @staticmethod
    def name() -> str:
        """return a normalized CPU model string from platform-specific sources."""
        try:
            if sys.platform == "darwin":
                s =subprocess.run(
                    ["sysctl","-n","machdep.cpu.brand_string"],capture_output=True,text=True
                ).stdout.strip()
                if s:
                    return CPUInfo._clean(s)
            elif sys.platform.startswith("linux"):
                # Parse /proc/cpuinfo for the first "model name" entry
                p = Path("/proc/cpuinfo")
                if p.exists():
                    for line in p.read_text(errors="ignore").splitlines():
                        if "model name" in line:
                            return CPUInfo._clean(line.split(":", 1)[1])
                        
            elif sys.platform.startswith("win"):
                try:
                    import winreg as wr

                    with wr.OpenKey(wr.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                        val, _ = wr.QueryValueEx(k, "ProcessorNameString")
                        if val:
                            return CPUInfo._clean(val)
                except Exception:
                    # Fall through to generic platform fallbacks on Windows registry access failure
                    pass
            # Generic platform fallbacks
            s = platform.processor() or getattr(platform.uname(), "processor", "") or platform.machine()
            return CPUInfo._clean(s or "Unknown CPU")
                

        except Exception:
            # Ensure 
            s = platform.processor() or platform.machine() or ""
            return CPUInfo._clean(s or "Unkonwn CPU")
    
    @staticmethod
    def _clean(s:str) -> str:
        """Normalize and prettify a raw CPU descriptor string."""
        s = re.sub(r"\s+", " ", s.strip())
        s = s.replace("(TM)", "").replace("(tm)", "").replace("(R)", "").replace("(r)", "").strip()
        if m := re.search(r"(Intel.*?i\d[\w-]*) CPU @ ([\d.]+GHz)", s, re.I):
            return f"{m.group(1)} {m.group(2)}"
        if m := re.search(r"(AMD.*?Ryzen.*?[\w-]*) CPU @ ([\d.]+GHz)", s, re.I):
            return f"{m.group(1)} {m.group(2)}"
        return s
    
    def __str__(self) -> str:
        """Return the normalized CPU name."""
        return self.name()
    
if __name__ == "__main__":
    print(CPUInfo.name())