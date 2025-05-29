import pandas as pd
import numpy as np
import io

def parse_markdown_table(md_table_string):
    """Parses a markdown table string into a pandas DataFrame more robustly."""
    raw_lines = md_table_string.strip().split('\n')
    
    table_lines_processed = []
    for line_content in raw_lines:
        s_line = line_content.strip()
        if not s_line: # Skip empty lines from input string
            continue
        
        # Ensure lines that are part of the table structure are consistently formatted
        # (e.g. start with | and end with | for splitting)
        # The provided markdown doesn't have trailing pipes on each line.
        if s_line.startswith('|'):
            # Heuristic for separator line: consists of '|', '-', ':', ' '
            # Example: |:---|:---:|---:| or |---|---|
            # If we remove all those chars, and it's empty, it's likely a separator
            temp_sep_check = s_line.replace('|','').replace('-','').replace(':','').replace(' ','')
            if not temp_sep_check:
                continue # Skip separator line
            
            # If line doesn't end with a pipe, add one for consistent splitting.
            if not s_line.endswith('|'):
                s_line += "|" 
            table_lines_processed.append(s_line)
        # else: # Line doesn't start with '|', probably not a table row. Skip.
            # print(f"Skipping non-table line: {s_line}")

    if not table_lines_processed:
        return pd.DataFrame()

    # Extract column names from the first valid table line
    header_cells_raw = table_lines_processed[0][1:-1].split('|') # Remove leading/trailing pipe, then split
    columns = [col.strip() for col in header_cells_raw]
    
    parsed_data = []
    # Iterate over data lines (skipping the header line)
    for line_idx in range(1, len(table_lines_processed)):
        data_cells_raw = table_lines_processed[line_idx][1:-1].split('|')
        row_data = [cell.strip() for cell in data_cells_raw]
        
        if len(row_data) == len(columns):
            parsed_data.append(row_data)
        # else:
            # print(f"Warning: Column mismatch. Expected {len(columns)}, got {len(row_data)} for line: {table_lines_processed[line_idx]}")

    df = pd.DataFrame(parsed_data, columns=columns)
    return df

def preprocess_dataframe(df, name_col="Аббревиатура"):
    """Renames 'Аббревиатура' to 'Название вещества' and removes redundant zero rows."""
    if df.empty:
        return df
    if name_col in df.columns:
        df = df.rename(columns={name_col: "Название вещества"})

    # Ensure numeric columns are numeric
    for col in ["Время (мин)", "Относительное время", "Площадь (мВ*с)", "Площадь (%)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    to_drop = []
    # Create a temporary key for unique substances that have non-zero entries
    non_zero_entries_keys = set()
    for idx, row in df.iterrows():
        if 'Время (мин)' in row and row['Время (мин)'] != 0 and not pd.isna(row['Время (мин)']):
            non_zero_entries_keys.add((row['Название вещества'], row['Компонент']))

    # Identify zero-time rows to drop if a non-zero entry for the same substance exists
    for idx, row in df.iterrows():
        if 'Время (мин)' in row and (row['Время (мин)'] == 0 or pd.isna(row['Время (мин)'])):
            if (row['Название вещества'], row['Компонент']) in non_zero_entries_keys:
                to_drop.append(idx)
    
    df_processed = df.drop(index=to_drop).reset_index(drop=True)
    return df_processed

# --- Data for Table 1 ---
md_table1 = """
| Аббревиатура | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 0.000      | 0.000              | 0.000         | 0.000
| 15:0         | Pentadecanoic acid, methyl ester                     | 0.000      | 0.000              | 0.000         | 0.000
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.380     | 0.887              | 80156350.506  | 2.064
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.355     | 0.937              | 3378602.774   | 0.087
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.574     | 0.948              | 960611.816    | 0.025
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.588     | 1.000              | 9691266.907   | 0.250
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 0.000      | 0.000              | 0.000         | 0.000
| 18:0         | Methyl stearate                                      | 22.271     | 1.137              | 3971641.800   | 0.102
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.680     | 1.158              | 1012101.101   | 0.026
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.683     | 1.209              | 623971250.882 | 16.069
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.790     | 1.215              | 129869123.809 | 3.344
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.689     | 1.311              | 432056345.756 | 11.127
| 20:0         | Eicosanoic acid, methyl ester                        | 27.492     | 1.403              | 2016042.903   | 0.052
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.950     | 1.427              | 91849645.028  | 2.365
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 0.000      | 0.000              | 0.000         | 0.000
| 20:1-13      | cis-13-Eicosenoic acid                               | 28.735     | 1.467              | 415314687.071 | 10.696
| 20:1-13      | cis-13-Eicosenoic acid                               | 28.875     | 1.474              | 21937153.246  | 0.565
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.473     | 1.556              | 8525070.851   | 0.220
| 22:0         | Docosanoic acid, methyl ester                        | 32.379     | 1.653              | 4967522.945   | 0.128
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 0.000      | 0.000              | 0.000         | 0.000
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 0.000      | 0.000              | 0.000         | 0.000
| 22:1-15      | 15-Docosenoic acid, methyl ester                     | 33.565     | 1.714              | 1725964012.972| 44.448
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.442     | 1.860              | 3429632.802   | 0.088
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.449     | 1.912              | 318785537.310 | 8.210
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.136     | 2.049              | 1312451.118   | 0.034
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.964     | 2.091              | 3898858.331   | 0.100
"""
df1_raw = parse_markdown_table(md_table1)
df1 = preprocess_dataframe(df1_raw.copy())

# --- Data for Table 2 ---
md_table2 = """
| Аббревиатура | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.561     | 0.693              | 413286.504    | 0.010
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.446     | 0.789              | 737185.420    | 0.018
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.370     | 0.887              | 106526458.406 | 2.568
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.348     | 0.937              | 3373789.331   | 0.081
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.541     | 0.947              | 1382266.507   | 0.033
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.573     | 1.000              | 14924468.757  | 0.360
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 20.157     | 1.030              | 528198.529    | 0.013
| 18:0         | Methyl stearate                                      | 22.282     | 1.138              | 5992150.862   | 0.144
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.658     | 1.158              | 1066574.708   | 0.026
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.669     | 1.210              | 679704954.060 | 16.384
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.780     | 1.215              | 105473266.132 | 2.542
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.697     | 1.313              | 554249434.665 | 13.360
| 20:0         | Eicosanoic acid, methyl ester                        | 27.492     | 1.405              | 1811989.339   | 0.044
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.925     | 1.427              | 106026260.009 | 2.556
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 0.000      | 0.000              | 0.000         | 0.000
| 20:1-13      | cis-13-Eicosenoic acid                               | 28.721     | 1.467              | 431133259.034 | 10.392
| 20:1-13      | cis-13-Eicosenoic acid                               | 28.853     | 1.474              | 25557817.527  | 0.616
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.455     | 1.556              | 12076032.917  | 0.291
| 22:0         | Docosanoic acid, methyl ester                        | 32.368     | 1.654              | 6354692.849   | 0.153
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.515     | 1.661              | 1273492.309   | 0.031
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 0.000      | 0.000              | 0.000         | 0.000
| 22:1-15      | 15-Docosenoic acid, methyl ester                     | 33.536     | 1.713              | 1673621396.958| 40.341
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.442     | 1.862              | 4300503.810   | 0.104
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.424     | 1.912              | 405475632.148 | 9.774
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.125     | 2.050              | 2109113.242   | 0.051
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.946     | 2.092              | 4535949.679   | 0.109
"""
df2_raw = parse_markdown_table(md_table2)
df2 = preprocess_dataframe(df2_raw.copy())

# --- Data for Table 3 ---
md_table3 = """
| Аббревиатура | Компонент                                            | Время (мин)| Относительное время| Площадь (мВ*с)| Площадь (%)
| 14:0         | Methyl tetradecanoate                                | 13.561     | 0.694              | 75470.888     | 0.002
| 15:0         | Pentadecanoic acid, methyl ester                     | 15.435     | 0.790              | 385971.261    | 0.011
| 16:0         | Hexadecanoic acid, methyl ester                      | 17.362     | 0.888              | 77695752.147  | 2.212
| 16:1-7       | 7-Hexadecenoic acid, methyl ester, (Z)-              | 18.326     | 0.937              | 4024201.800   | 0.115
| 16:1-9       | 9-Hexadecenoic acid, methyl ester, (Z)-              | 18.531     | 0.948              | 1003147.014   | 0.029
| 17:0         | Heptadecanoic acid, methyl ester                     | 19.552     | 1.000              | 12129050.438  | 0.345
| 16:2-7,10    | 7,10-Hexadecadienoic acid, methyl ester              | 20.136     | 1.029              | 222243.738    | 0.006
| 18:0         | Methyl stearate                                      | 22.243     | 1.138              | 5221707.162   | 0.149
| 16:3-7,10,13 | 7,10,13-Hexadecatrienoic acid, methyl ester          | 22.633     | 1.158              | 839608.892    | 0.024
| 18:1-9       | 9-Octadecenoic acid (Z)-, methyl ester               | 23.604     | 1.207              | 520822678.150 | 14.829
| 18:1-11      | 11-Octadecenoic acid, methyl ester, (Z)-             | 23.733     | 1.214              | 65294727.952  | 1.859
| 18:2-9,12    | 9,12-Octadecadienoic acid (Z,Z)-, methyl ester       | 25.632     | 1.311              | 407621826.036 | 11.606
| 20:0         | Eicosanoic acid, methyl ester                        | 27.449     | 1.406              | 1757565.016   | 0.050
| 18:3-9,12,15 | 9,12,15-Octadecatrienoic acid, methyl ester, (Z,Z,Z)-| 27.896     | 1.427              | 84733483.179  | 2.413
| 20:1-11      | 11-Eicosenoic acid, methyl ester                     | 28.660     | 1.466              | 347407704.720 | 9.892
| 20:1-13      | cis-13-Eicosenoic acid                               | 0.000      | 0.000              | 0.000         | 0.000
| 20:1-13      | cis-13-Eicosenoic acid                               | 28.807     | 1.473              | 15122869.229  | 0.431
| 20:2-11,14   | cis-11,14-Eicosadienoic acid, methyl ester           | 30.419     | 1.556              | 9294191.334   | 0.265
| 22:0         | Docosanoic acid, methyl ester                        | 32.296     | 1.652              | 7625544.178   | 0.217
| 20:3-11,14,17| 11,14,17-Eicosatrienoic acid, methyl ester           | 32.493     | 1.662              | 790459.118    | 0.023
| 22:1-13      | 13-Docosenoic acid, methyl ester, (Z)-               | 33.371     | 1.707              | 1503087196.149| 42.797
| 22:1-15      | 15-Docosenoic acid, methyl ester                     | 33.540     | 1.716              | 11154479.247  | 0.318
| 24:0         | Tetracosanoic acid, methyl ester                     | 36.410     | 1.861              | 3999800.562   | 0.114
| 24:1-15      | 15-Tetracosenoic acid, methyl ester                  | 37.395     | 1.912              | 426143325.590 | 12.134
| 26:0         | Hexacosanoic acid, methyl ester                      | 40.451     | 2.068              | 247011.150    | 0.007
| 26:1-17      | Methyl 17-hexacosenoate                              | 40.914     | 2.092              | 5409022.501   | 0.154
"""
df3_raw = parse_markdown_table(md_table3)
# Handle cases where 'Аббревиатура' might be 'Аббревиатура ' in df3 due to parsing
if 'Аббревиатура ' in df3_raw.columns and 'Аббревиатура' not in df3_raw.columns:
    df3_raw = df3_raw.rename(columns={'Аббревиатура ': 'Аббревиатура'})
df3 = preprocess_dataframe(df3_raw.copy())


reorders_log = [] 

merged_table_data = []

# Define the order of substances based on df1, then add any unique from df2, then df3
# This ensures all substances are captured and df1's order is prioritized.
all_substances_ordered = pd.concat([
    df1[['Название вещества', 'Компонент']],
    df2[['Название вещества', 'Компонент']],
    df3[['Название вещества', 'Компонент']]
]).drop_duplicates(subset=['Название вещества', 'Компонент']).reset_index(drop=True)


for _, ref_row in all_substances_ordered.iterrows():
    current_name = ref_row['Название вещества']
    current_comp = ref_row['Компонент']

    row_data_list = []
    for i, df_current in enumerate([df1, df2, df3]):
        match = df_current[(df_current['Название вещества'] == current_name) & 
                           (df_current['Компонент'] == current_comp)]
        if not match.empty:
            # If multiple matches (shouldn't happen after preprocessing for unique name/component), take first
            row_data_list.append(match.iloc[0]) 
        else:
            # If no match, create a dummy Series with NaNs for this substance in this df
            nan_data = {
                'Название вещества': current_name, 'Компонент': current_comp,
                'Время (мин)': np.nan, 'Относительное время': np.nan,
                'Площадь (мВ*с)': np.nan, 'Площадь (%)': np.nan
            }
            row_data_list.append(pd.Series(nan_data))
            
    times = [rd['Время (мин)'] for rd in row_data_list]
    rel_times = [rd['Относительное время'] for rd in row_data_list]
    areas_mvs = [rd['Площадь (мВ*с)'] for rd in row_data_list]
    areas_pct = [rd['Площадь (%)'] for rd in row_data_list]

    # Formatting: keep 0.000 as is, otherwise format to .3f or NaN
    fmt_val = lambda x: '0.000' if x == 0.0 else (f'{x:.3f}' if not pd.isna(x) else 'NaN')

    merged_table_data.append({
        "Название вещества": current_name,
        "Компонент": current_comp,
        "Время (мин)": f"[{','.join(map(fmt_val, times))}]",
        "Относительное время": f"[{','.join(map(fmt_val, rel_times))}]",
        "Площадь (мВ*с)": f"[{','.join(map(fmt_val, areas_mvs))}]",
        "Площадь (%)": f"[{','.join(map(fmt_val, areas_pct))}]"
    })

final_merged_df = pd.DataFrame(merged_table_data)

def sort_key_name(name_series):
    # Helper to extract sortable part from 'Название вещества'
    def get_sort_val(name):
        if pd.isna(name): return (9999, name) # Put NaNs last
        parts = str(name).split(':')[0]
        num_part = ''.join(filter(str.isdigit, parts))
        if num_part:
            return (int(num_part), name) # Sort by number, then by full name as tie-breaker
        return (9998, name) # Non-numeric names after numeric ones but before NaNs
    
    return pd.Series([get_sort_val(name) for name in name_series], index=name_series.index)

final_merged_df = final_merged_df.sort_values(
    by="Название вещества", 
    key=sort_key_name
).reset_index(drop=True)


reorders_df = pd.DataFrame(reorders_log)
if not reorders_df.empty:
    reorders_df = reorders_df[['Источник таблицы', 'Исходное Название вещества', 'Исходное Относительное время', 'Новое Название вещества', 'Новый Компонент']]

print("### Итоговая объединенная таблица")
print(final_merged_df.to_markdown(index=False))
print("\n### Таблица перестановок")
if not reorders_df.empty:
    print(reorders_df.to_markdown(index=False))
else:
    print("Перестановок не было.")
