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
    elif column_name in ["Площадь (мВ*с)", "Площадь (%)"]:
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
.Семена стадия цвет 1
| Название вещества   | Компонент                                             | Время (мин)            | Относительное время   | Площадь (мВ*с)                              | Площадь (%)            |
| 14:0                | Methyl tetradecanoate                                 | [13.557,0.000,13.557]  | [0.694,0.000,0.693]   | [315286.718,0.000,354807.159]               | [0.008,0.000,0.007]    |
| 15:0                | Pentadecanoic acid, methyl ester                      | [15.442,0.000,15.446]  | [0.790,0.000,0.790]   | [508916.331,0.000,649532.208]               | [0.013,0.000,0.012]    |
| 16:0                | Hexadecanoic acid, methyl ester                       | [17.359,17.362,17.355] | [0.888,0.888,0.888]   | [95327416.322,127102434.222,108099519.925]  | [2.380,2.510,2.058]    |
| 16:1-7              | 7-Hexadecenoic acid, methyl ester, (Z)-               | [18.333,18.330,18.330] | [0.938,0.937,0.937]   | [7115321.673,6810180.510,6071845.070]       | [0.178,0.134,0.116]    |
| 16:1-9              | 9-Hexadecenoic acid, methyl ester, (Z)-               | [18.538,18.538,18.531] | [0.948,0.948,0.948]   | [1212184.862,2159179.969,1255771.728]       | [0.030,0.043,0.024]    |
| 16:2-7,10           | 7,10-Hexadecadienoic acid, methyl ester               | [20.143,20.164,20.139] | [1.030,1.031,1.030]   | [363904.171,229692.474,575628.638]          | [0.009,0.005,0.011]    |
| 16:3-7,10,13        | 7,10,13-Hexadecatrienoic acid, methyl ester           | [22.629,22.637,22.637] | [1.158,1.157,1.158]   | [1086534.721,1934812.207,2057537.723]       | [0.027,0.038,0.039]    |
| 17:0                | Heptadecanoic acid, methyl ester                      | [19.548,19.559,19.555] | [1.000,1.000,1.000]   | [11984080.838,19786991.433,20732408.788]    | [0.299,0.391,0.395]    |
| 18:0                | Methyl stearate                                       | [22.246,22.239,22.253] | [1.138,1.137,1.138]   | [6814100.472,8271866.754,8849320.867]       | [0.170,0.163,0.169]    |
| 18:1-11             | 11-Octadecenoic acid, methyl ester, (Z)-              | [23.729,23.747,23.755] | [1.214,1.214,1.215]   | [79509665.613,119721598.968,84129021.670]   | [1.985,2.364,1.602]    |
| 18:1-9              | 9-Octadecenoic acid (Z)-, methyl ester                | [23.615,23.600,23.640] | [1.208,1.207,1.209]   | [605087742.384,733929947.060,806195839.396] | [15.109,14.491,15.351] |
| 18:2-9,12           | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester        | [25.650,25.654,25.654] | [1.312,1.312,1.312]   | [526064448.679,641150442.824,606517926.989] | [13.136,12.659,11.549] |
| 18:3-9,12,15        | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)- | [27.889,27.896,27.904] | [1.427,1.426,1.427]   | [112566469.986,137261188.199,120302956.909] | [2.811,2.710,2.291]    |
| 20:0                | Eicosanoic acid, methyl ester                         | [27.463,27.452,27.467] | [1.405,1.404,1.405]   | [2569859.968,2921500.749,3096827.606]       | [0.064,0.058,0.059]    |
| 20:1-11             | 11-Eicosenoic acid, methyl ester                      | [28.681,28.685,28.681] | [1.467,1.467,1.467]   | [457654956.561,500133281.018,537202946.118] | [11.428,9.875,10.229]  |
| 20:1-13             | cis-13-Eicosenoic acid                                | [28.814,28.814,28.835] | [1.474,1.473,1.475]   | [22237705.048,44187375.035,39356266.350]    | [0.555,0.872,0.749]    |
| 20:2-11,14          | cis-11,14-Eicosadienoic acid, methyl ester            | [30.419,30.415,30.426] | [1.556,1.555,1.556]   | [13169941.191,15177797.812,14952980.847]    | [0.329,0.300,0.285]    |
| 20:3-11,14,17       | 11,14,17-Eicosatrienoic acid, methyl ester            | [32.501,32.493,0.000]  | [1.663,1.661,0.000]   | [784567.347,1741631.822,0.000]              | [0.020,0.034,0.000]    |
| 22:0                | Docosanoic acid, methyl ester                         | [32.289,32.318,32.357] | [1.652,1.652,1.655]   | [7195929.628,9834040.257,7825035.740]       | [0.180,0.194,0.149]    |
| 22:1-13             | 13-Docosenoic acid, methyl ester, (Z)-                | [33.407,0.000,33.522]  | [1.709,0.000,1.714]   | [1618362717.524,0.000,2235474754.600]       | [40.411,0.000,42.568]  |
| 22:1-15             | 15-Docosenoic acid, methyl ester                      | [0.000,33.518,33.572]  | [0.000,1.714,1.717]   | [0.000,2148690117.400,16644633.928]         | [0.000,42.425,0.317]   |
| 24:0                | Tetracosanoic acid, methyl ester                      | [36.399,36.406,36.446] | [1.862,1.861,1.864]   | [5401582.464,5283874.155,7078305.808]       | [0.135,0.104,0.135]    |
| 24:1-15             | 15-Tetracosenoic acid, methyl ester                   | [37.391,37.417,37.449] | [1.913,1.913,1.915]   | [422845672.459,530207654.674,615428345.901] | [10.559,10.469,11.719] |
| 26:0                | Hexacosanoic acid, methyl ester                       | [40.068,40.215,40.254] | [2.050,2.056,2.059]   | [1365480.695,214126.131,60351.920]          | [0.034,0.004,0.001]    |
| 26:1-17             | Methyl 17-hexacosenoate                               | [40.914,40.921,40.931] | [2.093,2.092,2.093]   | [5211330.730,5662483.647,8178764.186]       | [0.130,0.112,0.156]    |
"""

processed_table_markdown = process_markdown_table(example_table_markdown)
print(processed_table_markdown)