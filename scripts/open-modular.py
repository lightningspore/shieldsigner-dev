#!/usr/bin/env python3
"""Open the modular project in the project's pinned KiCad application."""
from pathlib import Path
import runpy,subprocess
ROOT=Path(__file__).resolve().parents[1];cli=runpy.run_path(str(ROOT/'scripts/kicad.py'))['cli']()
subprocess.run(['open','-a',str(cli.parent.parent.parent),str(ROOT/'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pro')],check=True)
