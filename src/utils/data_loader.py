import pandas as pd
from typing import Tuple, Optional

class DataLoader:
    """
    Handles data file loading, validation, and schema extraction.
    Supports CSV and XLSX files up to 10MB.
    """
    
    MAX_FILE_SIZE_MB = 10
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 10MB in bytes
    SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls']
    
    def __init__(self):
        self.current_df: Optional[pd.DataFrame] = None
        self.file_name: Optional[str] = None


    def _get_extension(self, file_name: str) -> str:
        """
        Get file extension.
        """
        if '.' in file_name:
            return '.' + file_name.rsplit('.', 1)[-1].lower()
        return ''


    def validate_file(self, file_name: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file.
        
        Args:
            file_name: Name of the uploaded file
            file_size: Size of the file in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size > self.MAX_FILE_SIZE_BYTES:
            return False, f"File size exceeds {self.MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file."
        
        extension = self._get_extension(file_name)
        if extension not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type. Please upload a CSV or XLSX file."
        
        return True, ""


    def load_file(self, file_data: BytesIO, file_name: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Load data from uploaded file.
        
        Args:
            file_data: File data as BytesIO
            file_name: Name of the file
            
        Returns:
            Tuple of (success, message, dataframe)
        """
        try:
            extension = self._get_extension(file_name)
            
            if extension == '.csv':
                df = pd.read_csv(file_data)
            elif extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_data)
            else:
                return False, "Unsupported file format.", None
            
            if df.empty:
                return False, "The uploaded file is empty.", None
            
            self.current_df = df
            self.file_name = file_name
            
            return True, f"Successfully loaded {len(df)} rows and {len(df.columns)} columns.", df
            
        except pd.errors.EmptyDataError:
            return False, "The file is empty or has no valid data.", None
        except pd.errors.ParserError as e:
            return False, f"Error parsing file: {str(e)}", None
        except Exception as e:
            return False, f"Error loading file: {str(e)}", None


    def get_schema(self, df: Optional[pd.DataFrame] = None) -> str:
        """
        Extract and format the data schema.
        
        Args:
            df: DataFrame to extract schema from (uses current_df if None)
            
        Returns:
            Formatted schema string
        """
        if df is None:
            df = self.current_df
        
        if df is None:
            return "No data loaded."
        
        schema_parts = ["COLUMNS AND DATA TYPES:"]
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].count()
            total = len(df)
            null_pct = ((total - non_null) / total * 100) if total > 0 else 0
            
            # Get sample values
            sample_values = df[col].dropna().head(3).tolist()
            sample_str = ", ".join([str(v)[:30] for v in sample_values])
            
            schema_parts.append(
                f"  - {col} ({dtype}): {non_null}/{total} non-null | Sample: [{sample_str}]"
            )
        
        return "\n".join(schema_parts)
    

    def get_dataframe_info(self, df: Optional[pd.DataFrame] = None) -> str:
        """
        Get summary information about the dataframe.
        
        Args:
            df: DataFrame to get info from (uses current_df if None)
            
        Returns:
            Formatted info string
        """
        if df is None:
            df = self.current_df
        
        if df is None:
            return "No data loaded."
        
        info_parts = [
            f"Total Rows: {len(df)}",
            f"Total Columns: {len(df.columns)}",
            f"Column Names: {', '.join(df.columns.tolist())}",
        ]
        
        return "\n".join(info_parts)