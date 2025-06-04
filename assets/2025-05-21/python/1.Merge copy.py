import re
import pandas as pd
from io import StringIO

def parse_table_block(block_text_with_dot_prefix):
    lines = block_text_with_dot_prefix.strip().split('\n')
    title_line = lines[0]
    
    experiment_title = title_line # Default if regex doesn't match
    match = re.match(r"(.+?)\s*\[\d+\]\s*(.*)", title_line)
    if match:
        base_title_part1 = match.group(1).strip()
        base_title_part2 = match.group(2).strip() # Corrected: group 2
        if base_title_part1 and base_title_part2:
            experiment_title = f"{base_title_part1} {base_title_part2}"
        elif base_title_part1:
            experiment_title = base_title_part1
        elif base_title_part2: # Should not happen with the regex, but for safety
             experiment_title = base_title_part2
        # If both are empty, experiment_title remains title_line
    
    table_content_lines = [line for line in lines[1:] if line.strip().startswith('|')]
    
    column_mapping_rus_to_eng = {
        'Обозначение': 'Designation', 'Компонент': 'Component',
        'Время (мин)': 'Time_min', 'Относительное время': 'Relative_Time',
        'Площадь (мВ*с)': 'Area_mVs', 'Площадь (%)': 'Area_percent'
    }
    
    if not table_content_lines:
        empty_df = pd.DataFrame(columns=list(column_mapping_rus_to_eng.values()))
        return experiment_title, empty_df

    header_rus = [h.strip() for h in table_content_lines[0].strip('|').split('|')]
    
    data_rows = []
    if len(table_content_lines) > 1:
        for data_line_str in table_content_lines[1:]:
            cells = [cell.strip() for cell in data_line_str.strip('|').split('|')]
            if len(cells) == len(header_rus):
                data_rows.append(cells)

    df = pd.DataFrame(data_rows, columns=header_rus)
    df.rename(columns=column_mapping_rus_to_eng, inplace=True)
    
    numeric_cols_to_convert = ['Time_min', 'Relative_Time', 'Area_mVs', 'Area_percent']
    for col_eng in numeric_cols_to_convert:
        if col_eng in df.columns:
            df[col_eng] = pd.to_numeric(df[col_eng], errors='coerce').fillna(0.0)
        else:
            df[col_eng] = 0.0 
            
    # Ensure all standard columns are present, even if not in source (e.g. 'Component' if table was only numeric)
    for std_col_eng in column_mapping_rus_to_eng.values():
        if std_col_eng not in df.columns:
            if std_col_eng in numeric_cols_to_convert:
                 df[std_col_eng] = 0.0
            else: # Text columns like Designation, Component
                 df[std_col_eng] = pd.Series(dtype='object')


    return experiment_title, df

def process_experiment_data(text_input: str):
    blocks = text_input.strip().split('.Семена') 
    
    parsed_tables = []
    experiment_title_final = ""
    
    actual_blocks_content = [block_content for block_content in blocks if block_content.strip()]
    
    if not actual_blocks_content:
        print("No data blocks found.")
        return

    num_replicates = 0
    for i, block_content in enumerate(actual_blocks_content):
        full_block_text = ".Семена" + block_content 
        
        title_from_block, df = parse_table_block(full_block_text)
        
        required_cols_eng = ['Designation', 'Component', 'Time_min', 'Relative_Time', 'Area_mVs', 'Area_percent']
        if not all(col in df.columns for col in required_cols_eng):
            # This case should be less likely now with parse_table_block ensuring columns
            print(f"Warning: Table from block {i+1} (title: '{title_from_block}') seems malformed post-parsing. Ensuring standard columns.")
            temp_df = pd.DataFrame(columns=required_cols_eng)
            for col in required_cols_eng:
                if col in df.columns:
                    temp_df[col] = df[col]
                elif col in ['Time_min', 'Relative_Time', 'Area_mVs', 'Area_percent']:
                    temp_df[col] = pd.Series(dtype='float64')
                else:
                    temp_df[col] = pd.Series(dtype='object')
            df = temp_df.fillna({'Time_min': 0.0, 'Relative_Time': 0.0, 'Area_mVs': 0.0, 'Area_percent': 0.0})


        df['replicate_id'] = i + 1 
        parsed_tables.append(df)
        if not experiment_title_final: 
            experiment_title_final = title_from_block
        num_replicates +=1

    if not parsed_tables:
        print("No valid tables could be parsed and processed from the input.")
        return
    
    if not experiment_title_final and actual_blocks_content: # Fallback for title
         first_block_title_line = (".Семена" + actual_blocks_content[0].strip()).split('\n')[0]
         match = re.match(r"(.+?)\s*\[\d+\]\s*(.*)", first_block_title_line)
         if match:
            base_title_part1 = match.group(1).strip()
            base_title_part2 = match.group(2).strip()
            if base_title_part1 and base_title_part2: experiment_title_final = f"{base_title_part1} {base_title_part2}"
            elif base_title_part1: experiment_title_final = base_title_part1
            else: experiment_title_final = first_block_title_line
         else:
            experiment_title_final = first_block_title_line

    all_data = pd.concat(parsed_tables, ignore_index=True)

    if 'Designation' not in all_data.columns or all_data['Designation'].isnull().all():
        print(f"{experiment_title_final}\nColumn 'Обозначение' (Designation) not found or empty. Cannot group.")
        return

    all_data.dropna(subset=['Designation'], inplace=True) # Remove rows where Designation is NaN
    if all_data.empty:
        print(f"{experiment_title_final}\nNo data rows with valid 'Обозначение' (Designation) to process.")
        return

    grouped = all_data.groupby('Designation')
    output_rows = []
    warnings_component_names = []
    avg_relative_times_per_group = {}

    for name, group in grouped:
        component_names = group['Component'].dropna().unique()
        canonical_component = component_names[0] if len(component_names) > 0 else "N/A"
        
        if len(component_names) > 1:
             warnings_component_names.append(f"Warning for Designation '{name}': Multiple component names found: {list(component_names)}. Using '{canonical_component}'.")

        row_data = {
            'Designation': name, 'Component': canonical_component,
            'Time_min': [], 'Relative_Time': [],
            'Area_mVs': [], 'Area_percent': []
        }
        
        replicate_data_map = {}
        for _, r_row in group.iterrows():
            replicate_data_map[r_row['replicate_id']] = {
                'Time_min': float(r_row.get('Time_min', 0.0)),
                'Relative_Time': float(r_row.get('Relative_Time', 0.0)),
                'Area_mVs': float(r_row.get('Area_mVs', 0.0)),
                'Area_percent': float(r_row.get('Area_percent', 0.0))
            }

        for rep_idx in range(1, num_replicates + 1):
            data = replicate_data_map.get(rep_idx, {
                'Time_min': 0.0, 'Relative_Time': 0.0, 
                'Area_mVs': 0.0, 'Area_percent': 0.0
            })
            row_data['Time_min'].append(data['Time_min'])
            row_data['Relative_Time'].append(data['Relative_Time'])
            row_data['Area_mVs'].append(data['Area_mVs'])
            row_data['Area_percent'].append(data['Area_percent'])
                
        output_rows.append(row_data)
        
        non_zero_rel_times = [rt for rt in row_data['Relative_Time'] if rt > 0]
        if non_zero_rel_times:
            avg_relative_times_per_group[name] = sum(non_zero_rel_times) / len(non_zero_rel_times)

    final_df = pd.DataFrame(output_rows)
    if final_df.empty:
        print(f"{experiment_title_final}\nNo data to display after grouping.")
        return

    final_df['sort_key'] = final_df['Relative_Time'].apply(
        lambda x: sum(y for y in x if y > 0) / len([y for y in x if y > 0]) if any(y > 0 for y in x) else float('inf')
    )
    final_df.sort_values(by='sort_key', inplace=True)
    final_df.drop(columns=['sort_key'], inplace=True)

    reassignment_warnings = []
    REL_TIME_OUTLIER_THRESHOLD_ABS = 0.05 
    REL_TIME_CLOSENESS_TO_OTHER_GROUP_THRESHOLD = 0.01

    for _, merged_row in final_df.iterrows():
        designation = merged_row['Designation']
        current_rel_times = merged_row['Relative_Time']
        
        non_zero_current_rel_times = [rt for rt in current_rel_times if rt > 0]
        if not non_zero_current_rel_times: continue
        mean_current_rel_time = sum(non_zero_current_rel_times) / len(non_zero_current_rel_times)

        for i, rt_val in enumerate(current_rel_times):
            if rt_val == 0: continue
            replicate_num = i + 1
            is_outlier_for_own_group = abs(rt_val - mean_current_rel_time) > REL_TIME_OUTLIER_THRESHOLD_ABS
            
            if is_outlier_for_own_group:
                for other_designation, other_avg_rt in avg_relative_times_per_group.items():
                    if other_designation == designation: continue
                    if abs(rt_val - other_avg_rt) < REL_TIME_CLOSENESS_TO_OTHER_GROUP_THRESHOLD:
                        reassignment_warnings.append(
                            f"Potential re-assignment: Replicate {replicate_num} for Designation '{designation}' "
                            f"(Relative Time: {rt_val:.3f}) is an outlier for its group (mean: {mean_current_rel_time:.3f}) "
                            f"and is very close to the average Relative Time of Designation '{other_designation}' (mean: {other_avg_rt:.3f})."
                        )
                        break 

    for col_format in ['Time_min', 'Relative_Time', 'Area_mVs', 'Area_percent']:
        final_df[col_format] = final_df[col_format].apply(lambda x: '[' + ','.join(f"{val:.3f}" for val in x) + ']')

    reverse_column_mapping = {
        'Designation': 'Обозначение', 'Component': 'Компонент',
        'Time_min': 'Время (мин)', 'Relative_Time': 'Относительное время',
        'Area_mVs': 'Площадь (мВ*с)', 'Area_percent': 'Площадь (%)'
    }
    final_df.rename(columns=reverse_column_mapping, inplace=True)

    print(experiment_title_final)
    print(final_df.to_markdown(index=False))
    
    if warnings_component_names:
        print("\nWarnings about component names:")
        for warning in warnings_component_names:
            print(warning)
            
    if reassignment_warnings:
        print("\nNotes on potential re-assignments based on Relative Time:")
        for warning in reassignment_warnings:
            print(warning)

user_input_text = """
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

process_experiment_data(user_input_text)