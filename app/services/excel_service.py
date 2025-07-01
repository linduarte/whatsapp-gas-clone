# app/services/excel_service.py
import pandas as pd
import io

class ExcelService:
    def process_excel_content(self, content: bytes, filename: str, target_month: str = None):
        """Process Excel file content and return formatted data
        
        Args:
            content: Excel file content in bytes
            filename: Name of the uploaded file
            target_month: Optional month filter (e.g., "01/2025", "02/2025")
        """
        try:
            # Read Excel from bytes with proper header handling
            excel_data = pd.read_excel(io.BytesIO(content), sheet_name="Gas_2025", header=0)
            
            print(f"Raw Excel data shape: {excel_data.shape}")
            print(f"Columns: {list(excel_data.columns)}")
            print(f"First few rows:\n{excel_data.head()}")
            
            # Clean and format the dataframe
            formatted_df = self._format_dataframe(excel_data)
            
            print(f"Formatted data shape: {formatted_df.shape}")
            
            # Filter by month if specified
            if target_month:
                formatted_df = self._filter_by_month(formatted_df, target_month)
                print(f"After month filter ({target_month}): {formatted_df.shape}")
            
            # Convert to dictionary format
            gas_data = []
            target_date = None
            
            for index, row in formatted_df.iterrows():
                try:
                    # Skip rows that might be headers or invalid data
                    data_leitura = str(row.get("Data Leitura", "")).strip()
                    apartamento = str(row.get("Apartamento", "")).strip()
                    
                    # Skip empty rows or header rows
                    if not data_leitura or data_leitura.lower() == "data leitura":
                        continue
                    if not apartamento or apartamento.lower() == "apartamento":
                        continue
                    
                    item = {
                        "data_leitura": data_leitura,
                        "apartamento": apartamento,
                        "leitura_atual": self._safe_float_convert(row.get("Leitura atual", 0)),
                        "consumo_m3": self._safe_float_convert(row.get("Consumo(m³)", 0)),
                        "calculo": self._safe_float_convert(row.get("Cálculo", 0)),
                        "valor_final_rs": self._safe_float_convert(row.get("Valor final(R$)", 0))
                    }
                    gas_data.append(item)
                    
                    # Set target date from first valid row
                    if target_date is None and item["data_leitura"]:
                        target_date = item["data_leitura"]
                        
                except Exception as row_error:
                    print(f"Skipping row {index} due to error: {str(row_error)}")
                    continue
            
            if not gas_data:
                raise Exception("No valid data found in Excel file")
            
            return {
                "target_date": target_date or "Data desconhecida",
                "data": gas_data
            }
            
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")
    
    def _safe_float_convert(self, value):
        """Safely convert value to float, handling various edge cases"""
        if pd.isna(value) or value is None:
            return 0.0
        
        # If it's already a number
        if isinstance(value, (int, float)):
            return float(value)
        
        # If it's a string, try to convert
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return 0.0
            
            # Remove common formatting characters
            value = value.replace(',', '.').replace('R$', '').replace('%', '').strip()
            
            try:
                return float(value)
            except ValueError:
                print(f"Warning: Could not convert '{value}' to float, using 0.0")
                return 0.0
        
        return 0.0
    
    def _format_dataframe(self, df):
        """Format dataframe with proper data types and column handling"""
        # Remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")].copy()
        
        # Remove any completely empty rows
        df = df.dropna(how='all')
        
        print(f"After cleanup, columns: {list(df.columns)}")
        print(f"After cleanup, shape: {df.shape}")
        
        # Format date column with error handling
        if "Data Leitura" in df.columns:
            try:
                df["Data Leitura"] = pd.to_datetime(
                    df["Data Leitura"], format="%d/%m/%Y", errors="coerce"
                )
                df["Data Leitura"] = df["Data Leitura"].apply(
                    lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else ""
                )
            except Exception as e:
                print(f"Warning: Error formatting date column: {e}")
        
        # Format numeric columns with error handling
        numeric_columns = ["Leitura atual", "Consumo(m³)", "Cálculo", "Valor final(R$)"]
        
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # Convert to numeric, replacing errors with NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Fill NaN with 0
                    df[col] = df[col].fillna(0)
                    # Round appropriately
                    if col == "Valor final(R$)":
                        df[col] = df[col].round(2)
                    else:
                        df[col] = df[col].round(4)
                except Exception as e:
                    print(f"Warning: Error formatting column {col}: {e}")
                    df[col] = 0  # Default to 0 if conversion fails
        
        return df
    
    def _filter_by_month(self, df, target_month):
        """Filter dataframe by specific month
        
        Args:
            df: DataFrame with formatted data
            target_month: Month to filter (e.g., "01/2025", "02/2025")
        """
        if "Data Leitura" not in df.columns:
            print("Warning: No 'Data Leitura' column found for month filtering")
            return df
        
        try:
            # Parse target month
            if "/" in target_month:
                month, year = target_month.split("/")
            else:
                # Assume current year if only month provided
                month = target_month.zfill(2)
                year = "2025"
            
            print(f"Filtering for month: {month}/{year}")
            
            # Create a copy to avoid warnings
            filtered_df = df.copy()
            
            # Convert Data Leitura to datetime for filtering
            filtered_df["Data_Leitura_Date"] = pd.to_datetime(
                filtered_df["Data Leitura"], format="%d/%m/%Y", errors="coerce"
            )
            
            # Filter by month and year
            mask = (
                (filtered_df["Data_Leitura_Date"].dt.month == int(month)) &
                (filtered_df["Data_Leitura_Date"].dt.year == int(year))
            )
            
            result_df = filtered_df[mask].copy()
            
            # Remove the temporary date column
            if "Data_Leitura_Date" in result_df.columns:
                result_df = result_df.drop("Data_Leitura_Date", axis=1)
            
            print(f"Found {len(result_df)} records for {month}/{year}")
            
            if len(result_df) == 0:
                available_dates = filtered_df["Data Leitura"].dropna().unique()
                print(f"No data found for {month}/{year}. Available dates: {list(available_dates)[:10]}...")
            
            return result_df
            
        except Exception as e:
            print(f"Error filtering by month: {e}")
            return df