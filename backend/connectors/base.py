from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Any

class BaseSourceConnector(ABC):
    """
    Base class for all future data source connectors (e.g., CSV, Web Scrapers, APIs).
    Enforces a standard ingestion interface.
    """
    
    def __init__(self, source_name: str, source_type: str):
        self.source_name = source_name
        self.source_type = source_type

    @abstractmethod
    def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches raw data from the source. Must be implemented by subclasses.
        Returns a list of raw dictionaries.
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Normalizes the raw data into the canonical Document schema.
        Must return a pandas DataFrame ready for DB ingestion.
        """
        pass
        
    def execute(self, **kwargs) -> pd.DataFrame:
        """
        Main execution pipeline for the connector.
        """
        raw = self.fetch_data(**kwargs)
        normalized_df = self.normalize(raw)
        
        # Add provenance metadata
        normalized_df['source'] = self.source_name
        normalized_df['source_type'] = self.source_type
        
        return normalized_df

class CSVConnector(BaseSourceConnector):
    """Example implementation of a CSV Connector."""
    
    def __init__(self):
        super().__init__("User Upload", "csv")
        
    def fetch_data(self, file_path: str) -> List[Dict[str, Any]]:
        df = pd.read_csv(file_path)
        return df.to_dict('records')
        
    def normalize(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        # For our standard CSV, it's mostly 1:1, but this is where column mapping happens
        df = pd.DataFrame(raw_data)
        return df
