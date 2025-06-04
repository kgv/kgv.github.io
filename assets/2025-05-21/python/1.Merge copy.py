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
.Семена(10 мм) {2024-07-04} [1] (600 uL 17:0)
| Обозначение | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0        | Methyl tetradecanoate                                | 21.897     | 0.840              | 30746.634     | 0.015
| 16:0        | Hexadecanoic acid, methyl ester                      | 24.524     | 0.940              | 7811236.013   | 3.894
| 16:1-7      | 7-Hexadecenoic acid, methyl ester, (Z)-              | 25.302     | 0.970              | 92171.643     | 0.046
| 16:1-11     | (Z)-Methyl hexadec-11-enoate                         | 25.452     | 0.976              | 57311.592     | 0.029
| 17:0        | Heptadecanoic acid, methyl ester                     | 26.090     | 1.000              | 3064570.458   | 1.528
| 18:0        | Methyl stearate                                      | 27.584     | 1.057              | 335235.800    | 0.167
| 18:1-9      | 9-Octadecenoic acid (Z)-, methyl ester               | 28.315     | 1.085              | 48527739.253  | 24.192
| 18:1-11     | 11-Octadecenoic acid, methyl ester                   | 28.426     | 1.089              | 1621458.511   | 0.808
| 18:2-9,12   | 9,12-Octadecadienoic acid, methyl ester              | 29.423     | 1.128              | 30522653.413  | 15.216
| 18:3-9,12,15| 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 30.652     | 1.175              | 7181567.131   | 3.580
| 20:1-11     | cis-Methyl 11-eicosenoate                            | 30.931     | 1.185              | 22645850.658  | 11.289
| 20:1-13     | cis-13-Eicosenoic acid                               | 31.042     | 1.190              | 279119.070    | 0.139
| 20:2-11,14  | 11,14-Eicosadienoic acid, methyl ester               | 31.895     | 1.222              | 333487.092    | 0.166
| 22:0        | Docosanoic acid, methyl ester                        | 32.662     | 1.252              | 328484.954    | 0.164
| 22:1-13     | 13-Docosenoic acid, methyl ester, (Z)-               | 33.221     | 1.273              | 64472314.518  | 32.140
| 22:2-13,16  | cis-13,16-Docasadienoic acid, methyl ester           | 34.042     | 1.305              | 254529.107    | 0.127
| 24:0        | Tetracosanoic acid, methyl ester                     | 34.701     | 1.330              | 165916.567    | 0.083
| 24:1-15     | 15-Tetracosenoic acid, methyl ester                  | 35.181     | 1.348              | 12871757.643  | 6.417

.Семена(10 мм) {2024-07-04} [2] (600 uL 17:0)
| Обозначение | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0        | Methyl tetradecanoate                                | 0.000      | 0.000              | 0.000         | 0.000
| 16:0        | Hexadecanoic acid, methyl ester                      | 24.567     | 0.940              | 7595876.505   | 3.663
| 16:1-7      | 7-Hexadecenoic acid, methyl ester, (Z)-              | 25.345     | 0.970              | 47568.852     | 0.023
| 16:1-11     | (Z)-Methyl hexadec-11-enoate                         | 0.000      | 0.000              | 0.000         | 0.000
| 17:0        | Heptadecanoic acid, methyl ester                     | 26.126     | 1.000              | 2419414.922   | 1.167
| 18:0        | Methyl stearate                                      | 27.627     | 1.057              | 384051.447    | 0.185
| 18:1-9      | 9-Octadecenoic acid (Z)-, methyl ester               | 28.362     | 1.086              | 54373182.915  | 26.223
| 18:1-11     | 11-Octadecenoic acid, methyl ester                   | 28.466     | 1.090              | 1755421.745   | 0.847
| 18:2-9,12   | 9,12-Octadecadienoic acid, methyl ester              | 29.459     | 1.128              | 28649135.836  | 13.817
| 18:3-9,12,15| 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 30.688     | 1.175              | 6701995.734   | 3.232
| 20:1-11     | cis-Methyl 11-eicosenoate                            | 30.967     | 1.185              | 24732268.357  | 11.928
| 20:1-13     | cis-13-Eicosenoic acid                               | 31.078     | 1.189              | 277626.013    | 0.134
| 20:2-11,14  | 11,14-Eicosadienoic acid, methyl ester               | 31.931     | 1.222              | 276469.302    | 0.133
| 22:0        | Docosanoic acid, methyl ester                        | 32.702     | 1.252              | 180264.708    | 0.087
| 22:1-13     | 13-Docosenoic acid, methyl ester, (Z)-               | 33.257     | 1.273              | 67457799.521  | 32.534
| 22:2-13,16  | cis-13,16-Docasadienoic acid, methyl ester           | 34.074     | 1.304              | 165023.558    | 0.080
| 24:0        | Tetracosanoic acid, methyl ester                     | 34.737     | 1.330              | 1523.203      | 0.001
| 24:1-15     | 15-Tetracosenoic acid, methyl ester                  | 35.214     | 1.348              | 12328812.513  | 5.946

.Семена(10 мм) {2024-07-04} [3] (600 uL 17:0)
| Обозначение | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0        | Methyl tetradecanoate                                | 21.951     | 0.839              | 64718.528     | 0.052
| 16:0        | Hexadecanoic acid, methyl ester                      | 24.589     | 0.940              | 5702247.753   | 4.549
| 16:1-7      | 7-Hexadecenoic acid, methyl ester, (Z)-              | 25.359     | 0.970              | 77764.222     | 0.062
| 16:1-11     | (Z)-Methyl hexadec-11-enoate                         | 0.000      | 0.000              | 0.000         | 0.000
| 17:0        | Heptadecanoic acid, methyl ester                     | 26.158     | 1.000              | 1632561.726   | 1.302
| 18:0        | Methyl stearate                                      | 27.652     | 1.057              | 566074.455    | 0.452
| 18:1-9      | 9-Octadecenoic acid (Z)-, methyl ester               | 28.491     | 1.089              | 867478.104    | 0.692
| 18:1-11     | 11-Octadecenoic acid, methyl ester                   | 28.380     | 1.085              | 28466366.453  | 22.709
| 18:2-9,12   | 9,12-Octadecadienoic acid, methyl ester              | 29.487     | 1.127              | 20736596.853  | 16.542
| 18:3-9,12,15| 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 30.720     | 1.174              | 4280139.433   | 3.414
| 20:1-11     | cis-Methyl 11-eicosenoate                            | 0.000      | 0.000              | 0.000         | 0.000
| 20:1-13     | cis-13-Eicosenoic acid                               | 30.996     | 1.185              | 13011698.117  | 10.380
| 20:2-11,14  | 11,14-Eicosadienoic acid, methyl ester               | 31.960     | 1.222              | 190115.024    | 0.152
| 22:0        | Docosanoic acid, methyl ester                        | 32.723     | 1.251              | 124286.490    | 0.099
| 22:1-13     | 13-Docosenoic acid, methyl ester, (Z)-               | 33.282     | 1.272              | 41869734.278  | 33.401
| 22:2-13,16  | cis-13,16-Docasadienoic acid, methyl ester           | 34.099     | 1.304              | 156215.032    | 0.125
| 24:0        | Tetracosanoic acid, methyl ester                     | 34.755     | 1.329              | 27096.738     | 0.022
| 24:1-15     | 15-Tetracosenoic acid, methyl ester                  | 35.242     | 1.347              | 7581444.163   | 6.048

.Семена(10 мм) {2024-07-04} [4] (600 uL 17:0)
| Обозначение | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0        | Methyl tetradecanoate                                | 0.000      | 0.000              | 0.000         | 0.000
| 16:0        | Hexadecanoic acid, methyl ester                      | 24.581     | 0.940              | 7272743.308   | 2.958
| 16:1-7      | 7-Hexadecenoic acid, methyl ester, (Z)-              | 25.359     | 0.970              | 138592.360    | 0.056
| 16:1-11     | (Z)-Methyl hexadec-11-enoate                         | 25.513     | 0.975              | 67118.790     | 0.027
| 17:0        | Heptadecanoic acid, methyl ester                     | 26.155     | 1.000              | 1976273.742   | 0.804
| 18:0        | Methyl stearate                                      | 27.656     | 1.057              | 350647.841    | 0.143
| 18:1-9      | 9-Octadecenoic acid (Z)-, methyl ester               | 28.487     | 1.089              | 1798501.383   | 0.732
| 18:1-11     | 11-Octadecenoic acid, methyl ester                   | 28.380     | 1.085              | 50307829.092  | 20.465
| 18:2-9,12   | 9,12-Octadecadienoic acid, methyl ester              | 29.487     | 1.127              | 35848507.259  | 14.583
| 18:3-9,12,15| 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 30.713     | 1.174              | 7491187.397   | 3.047
| 20:1-11     | cis-Methyl 11-eicosenoate                            | 31.110     | 1.189              | 595688.206    | 0.242
| 20:1-13     | cis-13-Eicosenoic acid                               | 30.996     | 1.185              | 28180452.441  | 11.463
| 20:2-11,14  | 11,14-Eicosadienoic acid, methyl ester               | 31.956     | 1.222              | 474378.507    | 0.193
| 22:0        | Docosanoic acid, methyl ester                        | 32.727     | 1.251              | 301260.120    | 0.123
| 22:1-13     | 13-Docosenoic acid, methyl ester, (Z)-               | 33.296     | 1.273              | 92595302.355  | 37.667
| 22:2-13,16  | cis-13,16-Docasadienoic acid, methyl ester           | 34.103     | 1.304              | 411142.132    | 0.167
| 24:0        | Tetracosanoic acid, methyl ester                     | 34.755     | 1.329              | 142080.580    | 0.058
| 24:1-15     | 15-Tetracosenoic acid, methyl ester                  | 35.246     | 1.348              | 17876618.480  | 7.272
"""

process_experiment_data(user_input_text)