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
.Семена(финальная стадия) [1] (500 uL 17:0)
| Обозначение  | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 0.000      | 0.000              | 0.000         | 0.000
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.449     | 0.790              | 164562.164    | 0.018
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.352     | 0.888              | 18095418.541  | 2.033
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.327     | 0.937              | 1188790.713   | 0.134
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.542     | 0.948              | 100363.510    | 0.011
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.550     | 1.000              | 11105152.753  | 1.247
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 0.000      | 0.000              | 0.000         | 0.000
| 18:0         | Methyl stearate                                      | 22.193     | 1.135              | 647007.662    | 0.073
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 0.000      | 0.000              | 0.000         | 0.000
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.494     | 1.202              | 142273090.961 | 15.981
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.690     | 1.212              | 6318416.694   | 0.710
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.541     | 1.306              | 114675624.359 | 12.881
| 20:0         | Eicosanoic acid, methyl ester                        | 27.419     | 1.403              | 329297.661    | 0.037
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.864     | 1.425              | 15323722.601  | 1.721
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.559     | 1.461              | 96850319.016  | 10.879
| 20:1-13      | cis-13-Eicosenoic acid                               | 28.780     | 1.472              | 1873075.620   | 0.210
| 20:1-13      | cis-13-Eicosenoic acid                               | 0.000      | 0.000              | 0.000         | 0.000
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.399     | 1.555              | 2040792.638   | 0.229
| 22:0         | Docosanoic acid, methyl ester                        | 32.136     | 1.644              | 1168794.195   | 0.131
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 0.000      | 0.000              | 0.000         | 0.000
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 33.230     | 1.700              | 385096233.385 | 43.257
| 22:1-15      | 15-Docosenoic acid, methyl ester                     | 0.000      | 0.000              | 0.000         | 0.000
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.279     | 1.856              | 688802.925    | 0.077
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.228     | 1.904              | 90960549.541  | 10.218
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.066     | 2.049              | 320072.198    | 0.036
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.909     | 2.093              | 1022358.651   | 0.115

.Семена(финальная стадия) [2] (500 uL 17:0)
| Обозначение      | Компонент                                            | Время (мин)  | Относительное время    | Площадь (мВ*с)       | Площадь (%)
| 14:0             | Methyl tetradecanoate                                | 13.590       | 0.695                  | 206.662              | 0.000
| 15:0             | Pentadecanoic acid, methyl ester                     | 15.453       | 0.790                  | 80036.723            | 0.009
| 16:0             | Hexadecanoic acid, methyl ester                      | 17.350       | 0.887                  | 18659290.881         | 2.124
| 16:1-7           | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.337       | 0.938                  | 1105864.437          | 0.126
| 16:1-9           | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.540       | 0.948                  | 233196.243           | 0.027
| 17:0             | Heptadecanoic acid, methyl ester                     | 19.556       | 1.000                  | 10658723.616         | 1.213
| 16:2-7,10        | 7,10-Hexadecadienoic acid, methyl ester              | 0.000        | 0.000                  | 0.000                | 0.000
| 18:0             | Methyl stearate                                      | 22.178       | 1.134                  | 693600.753           | 0.079
| 16:3-7,10,13     | 7,10,13-Hexadecatrienoic acid, methyl ester          | 0.000        | 0.000                  | 0.000                | 0.000
| 18:1-9           | 9-Octadecenoic acid (Z)-, methyl ester               | 23.487       | 1.201                  | 149612906.755        | 17.030
| 18:1-11          | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.680       | 1.211                  | 7176358.063          | 0.817
| 18:2-9,12        | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.537       | 1.306                  | 117438017.171        | 13.368
| 20:0             | Eicosanoic acid, methyl ester                        | 27.406       | 1.401                  | 400218.283           | 0.046
| 18:3-9,12,15     | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.858       | 1.425                  | 16120881.038         | 1.835
| 20:1-11          | 11-Eicosenoic acid, methyl ester                     | 28.556       | 1.460                  | 94895815.317         | 10.802
| 20:1-13          | cis-13-Eicosenoic acid                               | 28.776       | 1.471                  | 1861030.587          | 0.212
| 20:1-13          | cis-13-Eicosenoic acid                               | 0.000        | 0.000                  | 0.000                | 0.000
| 20:2-11,14       | cis-11,14-Eicosadienoic acid, methyl ester           | 30.384       | 1.554                  | 1959783.677          | 0.223
| 22:0             | Docosanoic acid, methyl ester                        | 32.130       | 1.643                  | 1202387.717          | 0.137
| 20:3-11,14,17    | 11,14,17-Eicosatrienoic acid, methyl ester           | 0.000        | 0.000                  | 0.000                | 0.000
| 22:1-13          | 13-Docosenoic acid, methyl ester, (Z)-               | 33.218       | 1.699                  | 367641701.408        | 41.849
| 22:1-15          | 15-Docosenoic acid, methyl ester                     | 33.581       | 1.717                  | 63311.555            | 0.007
| 24:0             | Tetracosanoic acid, methyl ester                     | 36.279       | 1.855                  | 659379.065           | 0.075
| 24:1-15          | 15-Tetracosenoic acid, methyl ester                  | 37.224       | 1.903                  | 86858827.736         | 9.887
| 26:0             | Hexacosanoic acid, methyl ester                      | 40.062       | 2.049                  | 270109.685           | 0.031
| 26:1-17          | Methyl 17-hexacosenoate                              | 40.907       | 2.092                  | 914479.089           | 0.104

.Семена(финальная стадия) [3] (500 uL 17:0)
| Обозначение   | Компонент                                      | Время (мин) | Относительное время | Площадь (мВ*с)   | Площадь (%) |
|---------------|------------------------------------------------|-------------|---------------------|------------------|-------------|
| 14:0          | Methyl tetradecanoate                          | 13.549      | 0.693               | 103183.554       | 0.011       |
| 15:0          | Pentadecanoic acid, methyl ester               | 15.435      | 0.790               | 112824.628       | 0.012       |
| 16:0          | Hexadecanoic acid, methyl ester                | 17.340      | 0.888               | 21505641.817     | 2.221       |
| 16:1-7        | 7-Hexadecenoic acid, methyl ester, (Z)-        | 18.314      | 0.938               | 1257779.909      | 0.130       |
| 16:1-9        | 9-Hexadecenoic acid, methyl ester, (Z)-        | 18.511      | 0.948               | 308028.623       | 0.032       |
| 17:0          | Heptadecanoic acid, methyl ester               | 19.533      | 1.000               | 12873570.775     | 1.329       |
| 16:2-7,10     | 7,10-Hexadecadienoic acid, methyl ester        | 0.000       | 0.000               | 0.000            | 0.000       |
| 18:0          | Methyl stearate                                | 22.181      | 1.136               | 776177.239       | 0.080       |
| 16:3-7,10,13  | 7,10,13-Hexadecatrienoic acid, methyl ester    | 0.000       | 0.000               | 0.000            | 0.000       |
| 18:1-9        | 9-Octadecenoic acid (Z)-, methyl ester         | 23.487      | 1.202               | 161451430.702    | 16.670      |
| 18:1-11       | 11-Octadecenoic acid, methyl ester, (Z)-       | 23.674      | 1.212               | 6219263.821      | 0.642       |
| 18:2-9,12     | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester | 25.533      | 1.307               | 125408194.309    | 12.949      |
| 20:0          | Eicosanoic acid, methyl ester                  | 27.387      | 1.402               | 271107.652       | 0.028       |
| 18:3-9,12,15  | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)- | 27.850      | 1.426               | 17435265.467     | 1.800       |
| 20:1-11       | 11-Eicosenoic acid, methyl ester               | 28.544      | 1.461               | 104784842.279    | 10.819      |
| 20:1-13       | cis-13-Eicosenoic acid                         | 28.765      | 1.473               | 1086059.376      | 0.112       |
| 20:1-13       | cis-13-Eicosenoic acid                         | 0.000       | 0.000               | 0.000            | 0.000       |
| 20:2-11,14    | cis-11,14-Eicosadienoic acid, methyl ester     | 30.382      | 1.555               | 1968437.274      | 0.203       |
| 22:0          | Docosanoic acid, methyl ester                  | 32.122      | 1.644               | 1074969.024      | 0.111       |
| 20:3-11,14,17 | 11,14,17-Eicosatrienoic acid, methyl ester     | 0.000       | 0.000               | 0.000            | 0.000       |
| 22:1-13       | 13-Docosenoic acid, methyl ester, (Z)-         | 33.234      | 1.701               | 418498259.434    | 43.211      |
| 22:1-15       | 15-Docosenoic acid, methyl ester               | 0.000       | 0.000               | 0.000            | 0.000       |
| 24:0          | Tetracosanoic acid, methyl ester               | 36.281      | 1.857               | 427537.874       | 0.044       |
| 24:1-15       | 15-Tetracosenoic acid, methyl ester            | 37.230      | 1.906               | 92224264.129     | 9.522       |
| 26:0          | Hexacosanoic acid, methyl ester                | 40.051      | 2.050               | 205060.779       | 0.021       |
| 26:1-17       | Methyl 17-hexacosenoate                        | 40.884      | 2.093               | 501316.137       | 0.052       |
"""

process_experiment_data(user_input_text)