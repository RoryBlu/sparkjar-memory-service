"""Deprecated compatibility wrapper for hierarchical manager."""
import warnings
from .memory_manager import MemoryManager

warnings.warn(
    "HierarchicalMemoryManager is deprecated; use MemoryManager with hierarchy support",
    DeprecationWarning,
    stacklevel=2,
)

class HierarchicalMemoryManager(MemoryManager):
    """Deprecated alias for MemoryManager."""
    pass
