from logger import logger
import openpyxl
from openpyxl.utils import get_column_letter
from datetime import datetime
import math


class PreProcessingService:
    async def parse_excel_data(uploaded_file):
        """
        Parses an Excel file and returns a dict of sheet_name: list of lists,
        where the first row is headers (with 'Row' as the first column),
        and each subsequent row is [row_index, ...cell values...].
        Handles datetime columns by converting them to ISO strings.
        """
        try:
            logger.info(f"Processing Excel extraction as list of lists..")
            wb = openpyxl.load_workbook(uploaded_file, data_only=True)
            extracted_data = {}

            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                if sheet.sheet_state in ['hidden', 'veryHidden']:
                    continue

                # Get visible rows and columns
                visible_rows = [row[0].row for row in sheet.iter_rows() if not all(cell.value is None for cell in row)]
                visible_cols = [col_idx for col_idx in range(1, sheet.max_column + 1)
                                if any(sheet.cell(row=row_idx, column=col_idx).value is not None for row_idx in visible_rows)]

                if not visible_rows or not visible_cols:
                    continue

                # Prepare headers: "Row" + Excel column letters
                headers = ['Row'] + [get_column_letter(col) for col in visible_cols]
                sheet_data = [headers]

                # Data rows
                for row_idx in visible_rows:
                    row_data = [row_idx]
                    for col_idx in visible_cols:
                        value = sheet.cell(row=row_idx, column=col_idx).value
                        if isinstance(value, float):
                            value = math.ceil(value)
                        elif isinstance(value, str):
                            value = value.replace('\n', ' ')
                        elif isinstance(value, datetime):
                            value = value.isoformat()
                        row_data.append(value if value is not None else None)
                    sheet_data.append(row_data)

                extracted_data[sheet_name] = sheet_data

            return extracted_data

        except Exception as e:
            logger.error(f"PED-001: Error extracting visible data from Excel file: {e}")
            return {"ERROR": str(e)}
