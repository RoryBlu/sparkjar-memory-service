"""Deprecated compatibility wrapper."""
import warnings
from .memory_manager import MemoryManager

warnings.warn(
    "memory_manager_with_validation is deprecated; use MemoryManager instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["MemoryManager"]
