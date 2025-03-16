"""
Custom argument calculators for contract method calls.

This module provides an abstract base class for creating custom
argument calculators for ContractJobCustomArgs jobs.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ArgumentCalculator(ABC):
    """
    Abstract base class for custom argument calculators.
    
    Implement this class to create a custom argument calculator for
    ContractJobCustomArgs jobs.
    """
    
    @abstractmethod
    def calculate_args(self, input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Calculate arguments for a contract method call.
        
        Args:
            input_data: Optional input data provided by the job configuration
            
        Returns:
            List of arguments to pass to the contract method
        """
        pass


def import_calculator(module_path: str) -> Any:
    """
    Import a calculator module dynamically.
    
    Args:
        module_path: Path to the module relative to custom/args
        
    Returns:
        The imported module
    """
    import importlib.util
    import os
    import sys
    from pathlib import Path
    
    # Get the full path to the module
    base_dir = Path(__file__).parent
    module_file = base_dir / f"{module_path}.py"
    
    if not module_file.exists():
        raise FileNotFoundError(f"Calculator module not found: {module_file}")
    
    # Import the module
    module_name = f"custom.args.{module_path.replace('/', '.')}"
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_file}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    return module 