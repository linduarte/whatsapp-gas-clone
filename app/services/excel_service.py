"""excel_services.py"""

import io
from datetime import datetime
from typing import Optional

import pandas as pd  # type: ignore


class ExcelService:  # pylint: disable=too-few-public-methods
    """Service for processing gas Excel files in the WhatsApp gas clone app."""

    def __init__(self) -> None:
        """Initialize the Excel service."""
        return None

    def process_excel_content(
        self, content: bytes, target_month: Optional[str] = None
    ) -> dict:
        """
        Process Excel file content and return formatted data.

        Args:
            content (bytes): Excel file content in bytes.
            target_month (str, optional): Month filter (e.g., "01/2026", "02/2026").

        Returns:
            dict: {"target_date": str, "data": list}
        """
        try:
            # 1. Abre o arquivo temporariamente para espiar as abas disponíveis
            content_io = io.BytesIO(content)
            xl = pd.ExcelFile(content_io, engine="openpyxl")
            abas_disponiveis = xl.sheet_names

            # 2. Define o ano corrente do sistema como alvo padrão (Ex: 2026)
            ano_alvo = str(datetime.now().year)

            # 3. Se o usuário passou um filtro de mês/ano, extrai o ano escolhido
            if target_month and "/" in target_month:
                try:
                    ano_alvo = target_month.split("/")[-1].strip()
                except IndexError:
                    pass

            # 4. Monta o nome dinâmico esperado para a aba
            aba_esperada = f"Gas_{ano_alvo}"

            # 5. Fallback de Segurança: Se a aba calculada não existir, usa a primeira disponível
            if aba_esperada in abas_disponiveis:
                aba_final = aba_esperada
            else:
                # Ensure aba_final is always a string (sheet names can sometimes be non-str)
                aba_final = str(abas_disponiveis[0]) if abas_disponiveis else "Sheet1"
                print(f"⚠️ Aba '{aba_esperada}' não encontrada. Utilizando fallback: '{aba_final}'")

            print(f"📂 Abrindo dinamicamente a aba do Excel: {aba_final}")

            # 6. Carrega os dados da aba definida
            content_io.seek(0)
            excel_data = pd.read_excel(
                content_io, sheet_name=aba_final, header=0
            )
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

                    # Forçamos as chaves a corresponderem exatamente ao modelo Pydantic esperado pelo FastAPI
                    item = {
                        "data_leitura": data_leitura,
                        "apartamento": apartamento,
                        "leitura_atual": self._safe_float_convert(
                            row.get("Leitura atual", 0)
                        ),
                        "consumo_m3": self._safe_float_convert(
                            row.get("Consumo(m³)", 0)
                        ),
                        "calculo": self._safe_float_convert(row.get("Cálculo", 0)),
                        "valor_final_rs": round(
                            self._safe_float_convert(row.get("Valor final(R$)", 0)), 2
                        ),
                    }
                    gas_data.append(item)
                    if not target_date and data_leitura:
                        target_date = data_leitura
                except (TypeError, ValueError) as row_error:
                    print(f"Skipping row {index} due to error: {row_error}")
                    continue

            if not gas_data:
                raise ValueError("No valid data found in Excel file.")

            return {"target_date": target_date or "Data desconhecida", "data": gas_data}

        except (
            ValueError,
            OSError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            match e:
                case pd.errors.EmptyDataError() as ee:
                    raise ValueError(
                        f"Empty data error processing Excel file: {ee}"
                    ) from ee
                case pd.errors.ParserError() as pe:
                    raise ValueError(
                        f"Parser error processing Excel file: {pe}"
                    ) from pe
                case ValueError() as ve:
                    raise ValueError(f"Value error processing Excel file: {ve}") from ve
                case OSError() as oe:
                    raise OSError(f"OS error processing Excel file: {oe}") from oe
                case _:
                    raise ValueError(f"Error processing Excel file: {e}") from e

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
        return 0.0

    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format dataframe with proper data types and column handling.
        """
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")].copy()
        df = df.dropna(how="all")
        print(f"After cleanup, columns: {list(df.columns)}")
        print(f"After cleanup, shape: {df.shape}")

        if "Data Leitura" in df.columns:
            try:
                if not pd.api.types.is_datetime64_any_dtype(df["Data Leitura"]):
                    df["Data Leitura"] = pd.to_datetime(
                        df["Data Leitura"], format="%d/%m/%Y", errors="coerce"
                    )
                if isinstance(df["Data Leitura"], pd.Series):
                    df["Data Leitura"] = df["Data Leitura"].apply(
                        lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else ""
                    )
            except (ValueError, TypeError) as e:
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
                except (ValueError, TypeError) as e:
                    print(f"Warning: Error formatting column {col}: {e}")
                    df[col] = 0
        return df

    def _filter_by_month(self, df: pd.DataFrame, target_month: str) -> pd.DataFrame:
        """
        Filter dataframe by specific month.
        """
        if "Data Leitura" not in df.columns:
            print("Warning: No 'Data Leitura' column found for month filtering.")
            return df
        try:
            if "/" in target_month:
                month, year = target_month.split("/")
            else:
                month = target_month.zfill(2)
                year = str(datetime.now().year)
                
            print(f"Filtering for month: {month}/{year}")
            filtered_df = df.copy()
            
            filtered_df["Data_Leitura_Date"] = pd.to_datetime(
                filtered_df["Data Leitura"], format="%d/%m/%Y", errors="coerce"
            )
            
            date_col = filtered_df["Data_Leitura_Date"]
            if isinstance(date_col, pd.Series) and pd.api.types.is_datetime64_any_dtype(
                date_col
            ):
                mask = (date_col.dt.month == int(month)) & (
                    date_col.dt.year == int(year)
                )
                result_df = filtered_df.loc[mask].copy()
            elif isinstance(date_col, pd.Timestamp):
                if (
                    pd.notnull(date_col)
                    and date_col.month == int(month)
                    and date_col.year == int(year)
                ):
                    result_df = filtered_df.copy()
                else:
                    result_df = filtered_df.iloc[0:0].copy()
            else:
                print(
                    "Warning: 'Data_Leitura_Date' is not datetime64, skipping month filter."
                )
                result_df = filtered_df.copy()
                
            if "Data_Leitura_Date" in result_df.columns:
                result_df = result_df.drop("Data_Leitura_Date", axis=1)
                
            print(f"Found {len(result_df)} records for {month}/{year}")
            if len(result_df) == 0:
                available_dates = filtered_df["Data Leitura"].dropna().unique()
                print(
                    f"No data found for {month}/{year}. Available dates: {list(available_dates)[:10]}..."
                )
            return result_df
        except (ValueError, TypeError) as e:
            match e:
                case ValueError() as ve:
                    print(f"Value error filtering by month: {ve}")
                case TypeError() as te:
                    print(f"Type error filtering by month: {te}")
            return df
        