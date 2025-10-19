import yaml
import csv
import json
from pathlib import Path
from typing import Union, List, Dict, Any


class InputHandler:
    """Handle multiple input file types: YAML, text, and CSV."""
    
    def __init__(self, file_path: str = None, file_type: str = None):
        """
        Initialize the input handler with a file path.
        
        Args:
            file_path: Path to the input file
            file_type: Specific file type to handle ('yaml', 'csv', 'text')
                      If provided, only this file type will be accepted
        """
        self.file_path = Path(file_path) if file_path else None
        self.allowed_file_type = file_type
        self.file_type = self._detect_file_type() if file_path else None
        
    def _detect_file_type(self) -> str:
        """Detect the file type based on extension."""
        extension = self.file_path.suffix.lower()
        
        if extension in ['.yaml', '.yml']:
            detected_type = 'yaml'
        elif extension == '.csv':
            detected_type = 'csv'
        elif extension in ['.txt', '.text']:
            detected_type = 'text'
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        # If a specific file type was specified, check if it matches
        if self.allowed_file_type and detected_type != self.allowed_file_type:
            raise ValueError(
                f"File type mismatch: Expected '{self.allowed_file_type}' "
                f"but got '{detected_type}'. Only {self.allowed_file_type} files are accepted."
            )
        
        return detected_type
    
    def read(self) -> Union[str, List, Dict]:
        """
        Read the file based on its type.
        
        Returns:
            Content of the file in appropriate format
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.file_type == 'yaml':
            return self._read_yaml()
        elif self.file_type == 'csv':
            return self._read_csv()
        elif self.file_type == 'text':
            return self._read_text()
    
    def _read_yaml(self) -> Dict[str, Any]:
        """Read YAML file and return as dictionary."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _read_csv(self) -> List[Dict[str, str]]:
        """Read CSV file and return as list of dictionaries."""
        data = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        return data
    
    def _read_text(self) -> str:
        """Read text file and return as string."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    



# Example usage
if __name__ == "__main__":
    # Example: Read YAML file (make sure the file exists)
    try:
        yaml_handler = InputHandler('data/icp_config.yaml', file_type='yaml')
        yaml_data = yaml_handler.read()
        print("YAML data:", yaml_data)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    
    # Example: Only accept YAML files - will reject other types
    # Uncomment below to test file type restriction
    # try:
    #     yaml_only = InputHandler('data.csv', file_type='yaml')
    # except ValueError as e:
    #     print(f"Error: {e}")