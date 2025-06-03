import pandas as pd
import re
from io import StringIO
import difflib

# Constants for matching substances
REL_TIME_TOLERANCE_MATCH = 0.02  # Tolerance for relative time difference
TIME_TOLERANCE_MATCH = 0.2     # Tolerance for absolute time (min) difference
COMPONENT_SIMILARITY_THRESHOLD = 0.85 # Threshold for difflib component name similarity

def parse_markdown_table_to_df(table_str: str) -> pd.DataFrame:
    """Parses a string containing a Markdown table into a pandas DataFrame."""
    lines = table_str.strip().split('\n')
    if not lines or len(lines) < 2: # Need at least header and separator line
        return pd.DataFrame()

    header_line = lines[0]
    header = [h.strip() for h in header_line.strip('|').split('|')]
    
    data_lines = []
    # Data lines start from index 2 (skipping header and separator)
    for line_idx in range(2, len(lines)):
        line = lines[line_idx]
        if not line.strip() or not line.strip().startswith('|'): # Skip empty lines or lines not starting with |
            continue
        values = [v.strip() for v in line.strip('|').split('|')]
        if len(values) == len(header):
            data_lines.append(values)
    
    if not data_lines:
        return pd.DataFrame(columns=header)

    df = pd.DataFrame(data_lines, columns=header)

    # Convert numeric columns to appropriate types
    numeric_cols = ['Время (мин)', 'Относительное время', 'Площадь (мВ*с)', 'Площадь (%)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0) # Coerce errors to NaN, then fill with 0.0
    return df

def get_base_experiment_name(title: str) -> str:
    """Extracts the base name of an experiment from its title string."""
    name = title.strip()
    if name.startswith('.'): # Remove leading dot if present
        name = name[1:]
    # Remove replicate identifiers like "[1]", "[2]", etc.
    name = re.sub(r'\s*\[[^\]]*\]\s*', ' ', name).strip()
    name = re.sub(r'\s+', ' ', name) # Normalize multiple spaces to a single space
    return name

def are_components_similar(s1: str, s2: str, threshold: float = COMPONENT_SIMILARITY_THRESHOLD) -> bool:
    """Checks if two component name strings are similar enough."""
    if pd.isna(s1) and pd.isna(s2): return True
    if pd.isna(s1) or pd.isna(s2): return False
    s1_norm = str(s1).lower()
    s2_norm = str(s2).lower()
    return difflib.SequenceMatcher(None, s1_norm, s2_norm).ratio() >= threshold

def format_list_as_str(data_list: list) -> str:
    """Formats a list of numbers into a string like '[num1,num2,...]' with 3 decimal places."""
    return "[" + ",".join(f"{x:.3f}" if isinstance(x, (float, int)) else str(x) for x in data_list) + "]"

def process_experiment_tables(input_text: str) -> str:
    """
    Processes input text containing multiple experiment tables, merges replicates,
    and returns the result as a Markdown formatted string.
    """
    raw_blocks = input_text.strip().split('\n\n') 
    
    parsed_tables_by_experiment = {}

    for block in raw_blocks:
        block_lines = block.strip().split('\n')
        if not block_lines or not block_lines[0].strip().startswith('.'):
            continue 
        
        title = block_lines[0]
        table_markdown = "\n".join(block_lines[1:]) 
        
        base_name = get_base_experiment_name(title)
        df = parse_markdown_table_to_df(table_markdown)
        
        if not df.empty:
            if base_name not in parsed_tables_by_experiment:
                parsed_tables_by_experiment[base_name] = []
            parsed_tables_by_experiment[base_name].append(df)

    output_markdown_parts = []
    value_cols = ['Время (мин)', 'Относительное время', 'Площадь (мВ*с)', 'Площадь (%)']

    for exp_name, tables_data in parsed_tables_by_experiment.items():
        output_markdown_parts.append(f".{exp_name}")
        
        num_replicates = len(tables_data)
        if num_replicates == 0:
            output_markdown_parts.append("| Обозначение | Компонент | Время (мин) | Относительное время | Площадь (мВ*с) | Площадь (%) |\n|---|---|---|---|---|---|\n")
            continue

        merged_output_rows = []
        swapped_notifications = []
        component_similarity_doubts = []
        
        used_row_indices = [set() for _ in range(num_replicates)]

        for ref_rep_idx in range(num_replicates):
            ref_table = tables_data[ref_rep_idx]
            for ref_row_original_idx, ref_row_series in ref_table.iterrows():
                if ref_row_original_idx in used_row_indices[ref_rep_idx]:
                    continue 

                ref_row_dict = ref_row_series.to_dict()
                
                current_merged_data = {
                    "Обозначение": ref_row_dict["Обозначение"],
                    "Компонент": ref_row_dict["Компонент"], 
                }
                for v_col in value_cols: 
                    current_merged_data[v_col] = [0.0] * num_replicates 
                
                for v_col in value_cols:
                    current_merged_data[v_col][ref_rep_idx] = ref_row_dict[v_col]
                used_row_indices[ref_rep_idx].add(ref_row_original_idx)

                group_id_defining = ref_row_dict["Обозначение"]
                group_comp_defining = ref_row_dict["Компонент"] 
                group_ref_rt = ref_row_dict["Относительное время"]
                group_ref_t = ref_row_dict["Время (мин)"]

                for other_rep_idx in range(num_replicates):
                    if other_rep_idx == ref_rep_idx:
                        continue

                    other_table = tables_data[other_rep_idx]
                    
                    candidate_time_match = None
                    candidate_time_match_idx = -1
                    min_rt_diff_for_time_match = float('inf')

                    candidate_designation_match = None
                    candidate_designation_match_idx = -1

                    if group_ref_t != 0.0:
                        for other_row_idx, other_row_s in other_table.iterrows():
                            if other_row_idx in used_row_indices[other_rep_idx]: continue
                            other_row_d = other_row_s.to_dict()
                            if other_row_d["Время (мин)"] != 0.0:
                                rt_diff = abs(group_ref_rt - other_row_d["Относительное время"])
                                t_diff = abs(group_ref_t - other_row_d["Время (мин)"])
                                if rt_diff < REL_TIME_TOLERANCE_MATCH and t_diff < TIME_TOLERANCE_MATCH:
                                    if rt_diff < min_rt_diff_for_time_match:
                                        min_rt_diff_for_time_match = rt_diff
                                        candidate_time_match = other_row_d
                                        candidate_time_match_idx = other_row_idx
                    
                    if candidate_time_match is None:
                        for other_row_idx, other_row_s in other_table.iterrows():
                            if other_row_idx in used_row_indices[other_rep_idx]: continue
                            other_row_d = other_row_s.to_dict()
                            if other_row_d["Обозначение"] == group_id_defining:
                                candidate_designation_match = other_row_d
                                candidate_designation_match_idx = other_row_idx
                                break 
                    
                    chosen_match_row = None
                    chosen_match_idx = -1

                    if candidate_time_match:
                        chosen_match_row = candidate_time_match
                        chosen_match_idx = candidate_time_match_idx
                    elif candidate_designation_match:
                        chosen_match_row = candidate_designation_match
                        chosen_match_idx = candidate_designation_match_idx
                    
                    if chosen_match_row:
                        for v_col in value_cols:
                            current_merged_data[v_col][other_rep_idx] = chosen_match_row[v_col]
                        used_row_indices[other_rep_idx].add(chosen_match_idx)

                        if chosen_match_row["Обозначение"] != group_id_defining:
                            swapped_notifications.append(
                                f"Вещество '{chosen_match_row['Обозначение']}' (Компонент: {chosen_match_row['Компонент']}) из таблицы {other_rep_idx + 1} "
                                f"было сопоставлено с группой '{group_id_defining}' (Компонент: {group_comp_defining})."
                            )
                        elif not are_components_similar(chosen_match_row["Компонент"], group_comp_defining):
                            similarity_ratio = difflib.SequenceMatcher(None, str(chosen_match_row["Компонент"]).lower(), str(group_comp_defining).lower()).ratio()
                            component_similarity_doubts.append(
                                f"Компонент для '{group_id_defining}' в таблице {other_rep_idx + 1} ('{chosen_match_row['Компонент']}') "
                                f"отличается от компонента эталонного вещества группы ('{group_comp_defining}') (Сходство: {similarity_ratio:.2f})."
                            )
                merged_output_rows.append(current_merged_data)
        
        def sort_key_func(row_data):
            first_valid_rel_time = float('inf')
            for i in range(num_replicates):
                if i < len(row_data['Время (мин)']) and row_data['Время (мин)'][i] != 0.0:
                    if i < len(row_data['Относительное время']):
                        first_valid_rel_time = row_data['Относительное время'][i]
                        return (first_valid_rel_time, row_data['Обозначение']) 
            return (first_valid_rel_time, row_data['Обозначение']) 

        merged_output_rows.sort(key=sort_key_func)

        md_headers = ["Обозначение", "Компонент"] + value_cols
        output_markdown_parts.append("| " + " | ".join(md_headers) + " |")
        output_markdown_parts.append("|" + "---|" * len(md_headers))

        for merged_row_item in merged_output_rows:
            row_values_str = [
                str(merged_row_item["Обозначение"]),
                str(merged_row_item["Компонент"]),
                format_list_as_str(merged_row_item["Время (мин)"]),
                format_list_as_str(merged_row_item["Относительное время"]),
                format_list_as_str(merged_row_item["Площадь (мВ*с)"]),
                format_list_as_str(merged_row_item["Площадь (%)"])
            ]
            output_markdown_parts.append("| " + " | ".join(row_values_str) + " |")
        
        if swapped_notifications:
            output_markdown_parts.append("\nПерестановки:")
            for note in sorted(list(dict.fromkeys(swapped_notifications))): 
                output_markdown_parts.append(f"- {note}")
        
        if component_similarity_doubts:
            output_markdown_parts.append("\nСомнения по компонентам:")
            for note in sorted(list(dict.fromkeys(component_similarity_doubts))): 
                output_markdown_parts.append(f"- {note}")
        output_markdown_parts.append("") 

    return "\n".join(output_markdown_parts)

input_data = """
.Семена 1 мм [1] (100 uL 17:0)
| Обозначение      | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0             | Methyl tetradecanoate                                | 13.511     | 0.6924             | 913250.247    | 0.175
| 15:0             | Pentadecanoic acid, methyl ester                     | 15.395     | 0.7890             | 1169023.666   | 0.224
| 16:0             | Hexadecanoic acid, methyl ester                      | 17.312     | 0.8872             | 103507844.726 | 19.865
| 16:1-9           | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.480     | 0.9471             | 149794.435    | 0.029
| 17:0             | Heptadecanoic acid, methyl ester                     | 19.512     | 1.0000             | 99164738.463  | 19.032
| 18:0             | Methyl stearate                                      | 22.131     | 1.1342             | 6936205.827   | 1.331
| 16:3-7,10,13     | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.551     | 1.1558             | 1564720.340   | 0.300
| 18:1-9           | 9-Octadecenoic acid (Z)-, methyl ester               | 23.608     | 1.2099             | 1335682.868   | 0.256
| 18:1-11          | 11-Octadecenoic acid, methyl ester                   | 23.389     | 1.1987             | 31417125.608  | 6.030
| 19:0             | Nonadecanoic acid, methyl ester                      | 24.804     | 1.2712             | 383378.693    | 0.074
| 18:2-9,12        | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.460     | 1.3048             | 125576431.888 | 24.101
| 20:0             | Eicosanoic acid, methyl ester                        | 27.377     | 1.4031             | 580651.227    | 0.111
| 18:3-9,12,15     | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.818     | 1.4257             | 142018557.073 | 27.256
| 20:1-11          | 11-Eicosenoic acid, methyl ester                     | 28.481     | 1.4597             | 868250.867    | 0.167
| 22:0             | Docosanoic acid, methyl ester                        | 32.089     | 1.6446             | 1567195.325   | 0.301
| 20:3-11,14,17    | 11,14,17-Eicosatrienoic acid, methyl ester           | 32.440     | 1.6626             | 308532.857    | 0.059
| 22:1-13          | 13-Docosenoic acid, methyl ester, (Z)-               | 0.000      | 0.0000             | 0.000         | 0.000
| 24:0             | Tetracosanoic acid, methyl ester                     | 36.299     | 1.8603             | 1875248.748   | 0.360
| 24:1-15          | 15-Tetracosenoic acid, methyl ester                  | 37.187     | 1.9059             | 1457956.897   | 0.280
| 26:0             | Hexacosanoic acid, methyl ester                      | 40.122     | 2.0563             | 255673.470    | 0.049

.Семена 1 мм [2] (100 uL 17:0)
| Обозначение  | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.625     | 0.693              | 1256200.755   | 0.208
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.517     | 0.789              | 1428763.968   | 0.237
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.445     | 0.887              | 125287982.177 | 20.765
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.419     | 0.936              | 653132.031    | 0.108
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.670     | 1.000              | 95057686.972  | 15.754
| 18:0         | Methyl stearate                                      | 22.303     | 1.134              | 6806925.041   | 1.128
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.730     | 1.156              | 1773501.282   | 0.294
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.565     | 1.198              | 33670532.676  | 5.580
| 18:1-11      | 11-Octadecenoic acid, methyl ester                   | 23.783     | 1.209              | 2118031.646   | 0.351
| 19:0         | Nonadecanoic acid, methyl ester                      | 24.980     | 1.270              | 311641.509    | 0.052
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.632     | 1.303              | 158279369.562 | 26.232
| 20:0         | Eicosanoic acid, methyl ester                        | 27.542     | 1.399              | 745303.343    | 0.124
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.979     | 1.422              | 169045385.557 | 28.017
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.627     | 1.455              | 1112363.434   | 0.184
| 22:0         | Docosanoic acid, methyl ester                        | 33.210     | 1.688              | 208501.722    | 0.035
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.221     | 1.638              | 1488432.156   | 0.247
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 32.590     | 1.657              | 440791.633    | 0.073
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.410     | 1.851              | 1806542.100   | 0.299
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.298     | 1.896              | 1881968.010   | 0.312
| 26:0         | Hexacosanoic acid, methyl ester                      | 0.000      | 0.000              | 0.000         | 0.000

.Семена 1 мм [3] (100 uL 17:0)
| Обозначение  | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.633     | 0.693              | 1381815.398   | 0.200
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.521     | 0.788              | 1677823.700   | 0.243
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.456     | 0.886              | 131116179.233 | 19.015
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.419     | 0.935              | 1072319.098   | 0.156
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.691     | 1.000              | 144925035.386 | 21.017
| 18:0         | Methyl stearate                                      | 22.314     | 1.133              | 9300343.554   | 1.349
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.737     | 1.155              | 2326471.151   | 0.337
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.579     | 1.198              | 40434095.863  | 5.864
| 18:1-11      | 11-Octadecenoic acid, methyl ester                   | 23.790     | 1.208              | 1567756.936   | 0.227
| 19:0         | Nonadecanoic acid, methyl ester                      | 24.980     | 1.269              | 698050.739    | 0.101
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.646     | 1.303              | 156467268.186 | 22.691
| 20:0         | Eicosanoic acid, methyl ester                        | 27.538     | 1.399              | 1046702.772   | 0.152
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.986     | 1.421              | 186680547.914 | 27.073
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.627     | 1.454              | 1385905.020   | 0.201
| 22:0         | Docosanoic acid, methyl ester                        | 32.228     | 1.637              | 2509907.378   | 0.364
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.583     | 1.655              | 589650.312    | 0.086
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 33.217     | 1.687              | 802401.446    | 0.116
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.413     | 1.850              | 2780998.865   | 0.403
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.295     | 1.894              | 2455853.947   | 0.356
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.190     | 2.041              | 328773.224    | 0.048
"""

result_markdown = process_experiment_tables(input_data)
print(result_markdown)