
import pandas as pd
import io
from typing import Optional



class ExcelService:
    def process_excel_content(self, content: bytes, filename: str, target_month: Optional[str] = None):
        """
        Process Excel file content and return formatted data.

        Args:
            content (bytes): Excel file content in bytes.
            filename (str): Name of the uploaded file.
            target_month (str, optional): Month filter (e.g., "01/2025", "02/2025").

        Returns:
            dict: {"target_date": str, "data": list}
        """
        try:
            excel_data = pd.read_excel(io.BytesIO(content), sheet_name="Gas_2025", header=0)
            print(f"Raw Excel data shape: {excel_data.shape}")
            print(f"Columns: {list(excel_data.columns)}")
            print(f"First few rows:\n{excel_data.head()}")

            formatted_df = self._format_dataframe(excel_data)
            print(f"Formatted data shape: {formatted_df.shape}")

            if target_month:
                formatted_df = self._filter_by_month(formatted_df, target_month)
                print(f"After month filter ({target_month}): {formatted_df.shape}")

            gas_data = []
            target_date: str = ""

            for index, row in formatted_df.iterrows():
                try:
                    data_leitura = str(row.get("Data Leitura", "") or "").strip()
                    apartamento = str(row.get("Apartamento", "") or "").strip()
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
                        "valor_final_rs": round(self._safe_float_convert(row.get("Valor final(R$)", 0)), 2),
                    }
                    gas_data.append(item)
                    if not target_date and item["data_leitura"]:
                        target_date = str(item["data_leitura"])
                except Exception as row_error:
                    print(f"Skipping row {index} due to error: {row_error}")
                    continue

            if not gas_data:
                raise ValueError("No valid data found in Excel file.")

            return {"target_date": target_date or "Data desconhecida", "data": gas_data}

        except Exception as e:
            raise Exception(f"Error processing Excel file: {e}")

    def _safe_float_convert(self, value) -> float:
        """
        Safely convert value to float, handling various edge cases.
        Always returns a float.
        """
        if pd.isna(value) or value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return 0.0
            value = value.replace(",", ".").replace("R$", "").replace("%", "").strip()
            try:
                return float(value)
            except ValueError:
                print(f"Warning: Could not convert '{value}' to float, using 0.0")
                return 0.0
        # For any other type, return 0.0 to ensure float return type
        return 0.0

    def _format_dataframe(self, df):
        """
        Format dataframe with proper data types and column handling.
        """
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")].copy()
        df = df.dropna(how="all")
        print(f"After cleanup, columns: {list(df.columns)}")
        print(f"After cleanup, shape: {df.shape}")

        if "Data Leitura" in df.columns:
            try:
                # Convert to datetime, but only if the column is not already datetime
                if not pd.api.types.is_datetime64_any_dtype(df["Data Leitura"]):
                    df["Data Leitura"] = pd.to_datetime(df["Data Leitura"], format="%d/%m/%Y", errors="coerce")
                # Only use .dt on Series, not on scalars
                if isinstance(df["Data Leitura"], pd.Series):
                    df["Data Leitura"] = df["Data Leitura"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
            except Exception as e:
                print(f"Warning: Error formatting date column: {e}")

        numeric_columns = ["Leitura atual", "Consumo(m³)", "Cálculo", "Valor final(R$)"]
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    df[col] = df[col].fillna(0)
                    if col == "Valor final(R$)":
                        df[col] = df[col].round(2)
                    else:
                        df[col] = df[col].round(4)
                except Exception as e:
                    print(f"Warning: Error formatting column {col}: {e}")
                    df[col] = 0
        return df

    def _filter_by_month(self, df, target_month):
        """
        Filter dataframe by specific month.

        Args:
            df (pd.DataFrame): DataFrame with formatted data.
            target_month (str): Month to filter (e.g., "01/2025", "02/2025").

        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        if "Data Leitura" not in df.columns:
            print("Warning: No 'Data Leitura' column found for month filtering.")
            return df
        try:
            if "/" in target_month:
                month, year = target_month.split("/")
            else:
                month = target_month.zfill(2)
                year = "2025"
            print(f"Filtering for month: {month}/{year}")
            filtered_df = df.copy()
            # Convert to datetime for filtering, robustly
            filtered_df["Data_Leitura_Date"] = pd.to_datetime(filtered_df["Data Leitura"], format="%d/%m/%Y", errors="coerce")
            # Only use .dt if the column is a Series of datetime
            date_col = filtered_df["Data_Leitura_Date"]
            if isinstance(date_col, pd.Series) and pd.api.types.is_datetime64_any_dtype(date_col):
                mask = (
                    (date_col.dt.month == int(month)) &
                    (date_col.dt.year == int(year))
                )
                result_df = filtered_df.loc[mask].copy()
            elif isinstance(date_col, pd.Timestamp):
                # Single row DataFrame, handle as scalar
                if pd.notnull(date_col) and date_col.month == int(month) and date_col.year == int(year):
                    result_df = filtered_df.copy()
                else:
                    result_df = filtered_df.iloc[0:0].copy()  # Empty DataFrame
            else:
                print("Warning: 'Data_Leitura_Date' is not datetime64, skipping month filter.")
                result_df = filtered_df.copy()
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
