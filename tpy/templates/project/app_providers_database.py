"""
Project database provider instance.
"""

from pathlib import Path

from tpy.providers.factory import get_provider

db = get_provider(project_root=Path(__file__).resolve().parents[2])
