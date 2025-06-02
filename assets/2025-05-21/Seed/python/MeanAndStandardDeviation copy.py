import numpy as np
import ast # For safely evaluating string representations of lists

def calculate_stats_formatted(values_str: str, column_name: str) -> str:
    """
    Calculates mean and standard deviation for a list of values represented as a string.

    Args:
        values_str: A string representation of a list of numbers (e.g., "[1.0, 2.0, 0.0]").
        column_name: The name of the column, used to determine zero-handling rules.

    Returns:
        A string formatted as "mean ±std" or "mean ±std!" if a zero was handled.
        Returns "Error parsing value" or "NaN ±NaN" or "NaN ±NaN!" in case of issues.
    """
    try:
        # Safely evaluate the string to a Python list
        values = ast.literal_eval(values_str)
        if not isinstance(values, list):
            # Handle cases where the string might not be a list but a single number
            # For this problem, we expect list-like strings.
            # If it's a single number string, ast.literal_eval would convert it directly.
            # We'll wrap it in a list if it's not already one after eval.
            if isinstance(values, (int, float)):
                 values = [values]
            else: # Not a list or a number, problematic input
                return "Invalid list format"

    except (ValueError, SyntaxError, TypeError):
        return "Error parsing value"

    if not values: # Empty list after parsing
        return "NaN ±NaN"

    is_zero_present_in_original = 0.0 in values
    suffix = "!" if is_zero_present_in_original else ""

    if column_name in ["Время (мин)", "Относительное время"]:
        # Exclude zeros for these columns
        processed_values = [v for v in values if v != 0.0]
        if not processed_values: # All values were zero or list was empty
            return f"NaN ±NaN{suffix}" # Suffix is added if original list contained zero
    elif column_name in ["Масса, mg/g", "Площадь (мВ*с)", "Площадь (%)"]:
        # Include zeros for these columns
        processed_values = values
        # Suffix is added if original list contained zero, even if it's included
    else:
        # Should not happen if column names are as expected
        return "Unknown column type for calculation"

    # Calculate mean
    mean = np.mean(processed_values)

    # Calculate standard deviation with ddof=1 (sample standard deviation)
    if len(processed_values) < 2:
        std = 0.0 # Standard deviation is 0 for a single element or empty list (after processing)
    else:
        std = np.std(processed_values, ddof=1)

    if np.isnan(mean) or np.isnan(std):
         return f"NaN ±NaN{suffix}" # Fallback for any NaN results

    return f"{mean:.4f} ±{std:.5f}{suffix}"

def process_markdown_table(table_md: str) -> str:
    """
    Processes a markdown table according to specified statistical rules.

    Args:
        table_md: A string containing the markdown table.

    Returns:
        A string containing the processed markdown table.
    """
    lines = table_md.strip().split('\n')

    title = ""
    # Check if the first line is a title (does not start with '|')
    if lines and not lines[0].strip().startswith('|'):
        title = lines[0]
        lines = lines[1:] # Remove title line from table processing

    # Find the header line (first line starting with '|')
    header_line_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('|'):
            header_line_index = i
            break
    
    if header_line_index == -1:
        return "Error: No header row found in table."

    header_full_str = lines[header_line_index]
    # Data rows start after the header, skipping the separator line if present
    data_rows_str = []
    for i in range(header_line_index + 1, len(lines)):
        line_stripped = lines[i].strip()
        if line_stripped.startswith('|---'): # Skip markdown separator line
            continue
        if line_stripped.startswith('|'): # Valid data row
            data_rows_str.append(lines[i])


    # Parse header
    # Remove leading/trailing '|' and then split by '|'
    parsed_header = [h.strip() for h in header_full_str.strip('|').split('|')]

    # Columns that need statistical processing
    statistical_columns = ["Время (мин)", "Относительное время", "Площадь (мВ*с)", "Площадь (%)"]

    processed_data_rows = []
    for row_str in data_rows_str:
        if not row_str.strip(): # Skip empty lines
            continue
        
        # Parse data columns
        cols = [c.strip() for c in row_str.strip('|').split('|')]

        if len(cols) != len(parsed_header):
            # print(f"Warning: Skipping malformed row (cols {len(cols)} vs header {len(parsed_header)}): {row_str}")
            processed_data_rows.append(cols) # Add as is or handle error
            continue

        current_processed_row = []
        for i, cell_value in enumerate(cols):
            column_name = parsed_header[i]
            if column_name in statistical_columns:
                current_processed_row.append(calculate_stats_formatted(cell_value, column_name))
            else:
                current_processed_row.append(cell_value) # Keep non-statistical columns as is
        processed_data_rows.append(current_processed_row)

    # Reconstruct the markdown table
    output_md_parts = []
    if title:
        output_md_parts.append(title)
    
    output_md_parts.append("| " + " | ".join(parsed_header) + " |")

    for prow in processed_data_rows:
        output_md_parts.append("| " + " | ".join(map(str, prow)) + " |")
        
    return "\n".join(output_md_parts) + "\n"

# Example usage with the provided table:
example_table_markdown = """
.Масса суммарных липидов на грамм сухого остатка
| ID                        | Масса, mg/g
| Семена(1 mm)              | [38.48775, 36.66439, 52.65994]
| Семена(2 mm)              | [47.05845, 43.29127, 40.98081]
| Семена(4 mm)              | [46.47666, 43.95742, 37.68045]
| Семена(6 mm)              | [61.53812, 55.86447, 54.49826]
| Семена(7 mm)              | [101.78203, 102.71729, 96.38351]
| Семена(8 mm)              | [107.37259, 100.92379, 84.42243]
| Семена(9 mm)              | [114.13534, 91.18591, 73.79210]
| Семена(10 mm)             | [43.61103, 33.34860, 37.82067]
| Семена(цвет0)             | [289.26376, 241.34392, 214.97022]
| Семена(цвет1)             | [295.45700, 260.53532, 218.76392]
| Семена(цвет2)             | [199.53198, 515.30569, 422.00838]
| Семена(сухие)             | [304.51468, 312.14653, 337.65149]
| Семена(10 mm) {2024-07-04}| [209.81944, 223.17161, 210.00540, 377.41583]
"""

processed_table_markdown = process_markdown_table(example_table_markdown)
print(processed_table_markdown)