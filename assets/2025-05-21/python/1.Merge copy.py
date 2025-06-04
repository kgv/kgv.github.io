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
.Семена 7 мм [1] (300 uL 17:0)
| Обозначение  | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.615     | 0.693              | 963048.559    | 0.055
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.502     | 0.790              | 1249470.457   | 0.071
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.446     | 0.888              | 159115004.446 | 9.084
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.419     | 0.938              | 1788578.763   | 0.102
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.621     | 0.948              | 1942806.498   | 0.111
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.636     | 1.000              | 25443425.607  | 1.453
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 20.255     | 1.032              | 227692.803    | 0.013
| 18:0         | Methyl stearate                                      | 22.325     | 1.137              | 11995760.916  | 0.685
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.749     | 1.159              | 1346301.388   | 0.077
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.692     | 1.207              | 578498398.503 | 33.026
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.837     | 1.214              | 56018703.996  | 3.198
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.721     | 1.310              | 381405589.877 | 21.774
| 20:0         | Eicosanoic acid, methyl ester                        | 27.513     | 1.401              | 2520061.099   | 0.144
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 28.025     | 1.427              | 199621884.230 | 11.396
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.678     | 1.460              | 129199672.832 | 7.376
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.507     | 1.554              | 4460185.572   | 0.255
| 22:0         | Docosanoic acid, methyl ester                        | 32.184     | 1.639              | 2066517.644   | 0.118
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.599     | 1.660              | 408940.927    | 0.023
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 33.247     | 1.693              | 154423683.251 | 8.816
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.329     | 1.850              | 5574654.968   | 0.318
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.266     | 1.898              | 31506815.748  | 1.799
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.089     | 2.042              | 1214592.495   | 0.069
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.932     | 2.084              | 650457.043    | 0.037

.Семена 7 мм [2] (300 uL 17:0)
| Обозначение  | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.576     | 0.693              | 1126556.049   | 0.052
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.460     | 0.790              | 1913642.880   | 0.088
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.398     | 0.889              | 186754523.304 | 8.582
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.360     | 0.938              | 2345987.221   | 0.108
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.561     | 0.948              | 2214249.309   | 0.102
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.577     | 1.000              | 31560288.638  | 1.450
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 20.188     | 1.031              | 279807.640    | 0.013
| 18:0         | Methyl stearate                                      | 22.285     | 1.138              | 17326788.763  | 0.796
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.695     | 1.160              | 2293131.046   | 0.105
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.646     | 1.208              | 778511239.231 | 35.777
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.789     | 1.215              | 69368995.433  | 3.188
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.675     | 1.312              | 478500705.760 | 21.990
| 20:0         | Eicosanoic acid, methyl ester                        | 27.450     | 1.402              | 3593274.444   | 0.165
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.973     | 1.429              | 242413598.042 | 11.140
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.828     | 1.473              | 3305522.046   | 0.152
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.449     | 1.555              | 6227057.267   | 0.286
| 22:0         | Docosanoic acid, methyl ester                        | 32.130     | 1.641              | 4201832.256   | 0.193
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.555     | 1.663              | 831537.066    | 0.038
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 33.215     | 1.697              | 272285479.253 | 12.513
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.287     | 1.854              | 8056919.948   | 0.370
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.228     | 1.902              | 59638359.381  | 2.741
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.047     | 2.046              | 2020810.617   | 0.093
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.892     | 2.089              | 1226659.656   | 0.056

.Семена 7 мм [3] (300 uL 17:0)
| Обозначение  | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.574     | 0.694              | 954172.652    | 0.047
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.449     | 0.789              | 1533489.697   | 0.075
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.388     | 0.889              | 187766664.286 | 9.222
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.354     | 0.937              | 1914520.958   | 0.094
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.550     | 0.948              | 2415490.598   | 0.119
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.569     | 1.000              | 30467481.478  | 1.496
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 20.171     | 1.031              | 462881.103    | 0.023
| 18:0         | Methyl stearate                                      | 22.266     | 1.138              | 15840027.371  | 0.778
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.666     | 1.158              | 2117088.115   | 0.104
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.636     | 1.208              | 674215130.825 | 33.113
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.764     | 1.214              | 57427543.115  | 2.821
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.658     | 1.311              | 459664380.248 | 22.576
| 20:0         | Eicosanoic acid, methyl ester                        | 27.438     | 1.402              | 3626944.109   | 0.178
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.960     | 1.429              | 241847658.803 | 11.878
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.607     | 1.462              | 135750269.777 | 6.667
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.432     | 1.555              | 5799570.826   | 0.285
| 22:0         | Docosanoic acid, methyl ester                        | 32.097     | 1.640              | 3300296.159   | 0.162
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.527     | 1.662              | 649614.620    | 0.032
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 33.171     | 1.695              | 154305647.855 | 7.579
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.268     | 1.853              | 8057321.198   | 0.396
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.207     | 1.901              | 44135472.523  | 2.168
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.039     | 2.046              | 2571144.895   | 0.126
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.879     | 1.901              | 1253675.779   | 0.062
"""

process_experiment_data(user_input_text)