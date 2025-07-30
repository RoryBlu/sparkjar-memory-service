"""Deprecated compatibility wrapper for hierarchical manager."""
import warnings
from .memory_manager import MemoryManager

warnings.warn(
    "memory_manager_hierarchical_fixed is deprecated; use MemoryManager",
    DeprecationWarning,
    stacklevel=2,
)

class HierarchicalMemoryManager(MemoryManager):
    """Deprecated alias for MemoryManager."""
    pass
