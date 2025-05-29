import pandas as pd
import numpy as np
import io
from tabulate import tabulate as tabulate_function 
import tabulate as tabulate_module 

# --- Вспомогательная функция для комбинированного вывода "среднее ± ст.откл." с N знаками после запятой ---
def format_combined_stat_fixed_decimals(mean_val, std_val, decimal_places=4):
    """Форматирует среднее и ст.откл. до заданного количества знаков после запятой."""
    mean_str = f"{mean_val:.{decimal_places}f}" if pd.notnull(mean_val) else "NaN"
    
    if pd.notnull(std_val): # Включаем ст.откл. только если оно не NaN
        std_str = f"{std_val:.{decimal_places}f}"
        return f"{mean_str} ±{std_str}"
    else: # std_val is NaN (например, для N=1)
        return mean_str

# 1. Исходные данные в виде строки
table_string = """
| ID              | stem:[m_0], stem:[g]| stem:[m_1], stem:[g]| stem:[m_2], stem:[g]| stem:[m_3], stem:[g]| stem:[m_4], stem:[g]| stem:[DW], stem:[%]
| stem:[Лп_1]     | 2.4528              | 2.7169              | 0.2641              | 2.4760              | 0.0232              | 8.784551306
| stem:[Лп_2]     | 2.4676              | 2.7029              | 0.2353              | 2.4887              | 0.0211              | 8.967275818
| stem:[Лп_3]     | 2.4985              | 2.7396              | 0.2411              | 2.5203              | 0.0218              | 9.041891331
| stem:[Т_1]      | 2.4920              | 2.5513              | 0.0593              | 2.5009              | 0.0089              | 15.008431703
| stem:[Т_2]      | 2.4197              | 2.4822              | 0.0625              | 2.4294              | 0.0097              | 15.520000000
| stem:[Т_3]      | 2.4873              | 2.5488              | 0.0615              | 2.4967              | 0.0094              | 15.284552846
| stem:[П_1]      | 2.4707              | 2.4944              | 0.0237              | 2.4752              | 0.0045              | 18.987341772
| stem:[П_2]      | 2.4977              | 2.5187              | 0.0210              | 2.5016              | 0.0039              | 18.571428571
| stem:[П_3]      | 2.4687              | 2.4973              | 0.0286              | 2.4739              | 0.0052              | 18.181818182
| stem:[Лс_{1.1}] | 2.4922              | 2.5671              | 0.0749              | 2.5014              | 0.0092              | 12.283044059
| stem:[Лс_{1.2}] | 2.4202              | 2.5113              | 0.0911              | 2.4346              | 0.0144              | 15.806805708
| stem:[Лс_{1.3}] | 2.4876              | 2.6173              | 0.1297              | 2.5050              | 0.0174              | 13.415574399
| stem:[Лс_{2.1}] | 2.4915              | 2.6063              | 0.1148              | 2.5051              | 0.0136              | 11.846689895
| stem:[Лс_{2.2}] | 2.4197              | 2.5479              | 0.1282              | 2.4347              | 0.0150              | 11.700468019
| stem:[Лс_{2.3}] | 2.4872              | 2.5968              | 0.1096              | 2.5005              | 0.0133              | 12.135036496
| stem:[С_{1.1}]  | 2.4709              | 2.4928              | 0.0219              | 2.4743              | 0.0034              | 15.525114155
| stem:[С_{1.2}]  | 2.4980              | 2.5202              | 0.0222              | 2.5015              | 0.0035              | 15.765765766
| stem:[С_{1.3}]  | 2.4688              | 2.4914              | 0.0226              | 2.4724              | 0.0036              | 15.929203540
| stem:[С_{2.1}]  | 2.4709              | 2.5581              | 0.0872              | 2.4840              | 0.0131              | 15.022935780
| stem:[С_{2.2}]  | 2.4980              | 2.5698              | 0.0718              | 2.5088              | 0.0108              | 15.041782730
| stem:[С_{2.3}]  | 2.4688              | 2.5393              | 0.0705              | 2.4797              | 0.0109              | 15.460992908
| stem:[С_{4.1}]  | 2.4709              | 2.6000              | 0.1291              | 2.4900              | 0.0191              | 14.794732765
| stem:[С_{4.2}]  | 2.4978              | 2.6166              | 0.1188              | 2.5157              | 0.0179              | 15.067340067
| stem:[С_{4.3}]  | 2.4689              | 2.5892              | 0.1203              | 2.4874              | 0.0185              | 15.378221114
| stem:[С_{6.1}]  | 2.4713              | 2.7093              | 0.2380              | 2.5087              | 0.0374              | 15.714285714
| stem:[С_{6.2}]  | 2.4979              | 2.7177              | 0.2198              | 2.5326              | 0.0347              | 15.787079163
| stem:[С_{6.3}]  | 2.4690              | 2.6782              | 0.2092              | 2.5026              | 0.0336              | 16.061185468
| stem:[С_{7.1}]  | 2.4711              | 2.7615              | 0.2904              | 2.5213              | 0.0502              | 17.286501377
| stem:[С_{7.2}]  | 2.4981              | 2.7907              | 0.2926              | 2.5462              | 0.0481              | 16.438824333
| stem:[С_{7.3}]  | 2.4691              | 2.7323              | 0.2632              | 2.5135              | 0.0444              | 16.869300912
| stem:[С_{8.1.1}]| 2.4710              | 2.8566              | 0.3856              | 2.5373              | 0.0663              | 17.193983403
| stem:[С_{8.1.2}]| 2.4980              | 2.8474              | 0.3494              | 2.5600              | 0.0620              | 17.744705209
| stem:[С_{8.1.3}]| 2.4688              | 2.9301              | 0.4613              | 2.5566              | 0.0878              | 19.033167136
| stem:[С_{9.1}]  | 2.4875              | 3.0350              | 0.5475              | 2.6162              | 0.1287              | 23.506849315
| stem:[С_{9.2}]  | 2.4682              | 2.9901              | 0.5219              | 2.5749              | 0.1067              | 20.444529603
| stem:[С_{9.3}]  | 2.4988              | 3.0144              | 0.5156              | 2.6181              | 0.1193              | 23.138091544
| stem:[С_{10.1}] | 2.4708              | 3.1266              | 0.6558              | 2.6595              | 0.1887              | 28.774016468
| stem:[С_{10.2}] | 2.4980              | 3.2265              | 0.7285              | 2.6925              | 0.1945              | 26.6986960
| stem:[С_{10.3}] | 2.4688              | 3.1791              | 0.7103              | 2.6649              | 0.1961              | 27.608052935
| Семена(цвет0)_0 | 11.1785             | 11.5080             | 0.3295              | 11.3030             | 0.1245              | 37.784522003034901366
| Семена(цвет0)_1 | 11.8646             | 12.1720             | 0.3074              | 11.9812             | 0.1166              | 37.93103448275862069
| Семена(цвет0)_2 | 10.2125             | 10.5499             | 0.3374              | 10.3464             | 0.1339              | 39.685832839359810314
| Семена(цвет1)_0 | 20.9402             | 21.2763             | 0.3361              | 21.0695             | 0.1293              | 38.470693246057720916
| Семена(цвет1)_1 | 12.5027             | 12.8436             | 0.3409              | 12.6340             | 0.1313              | 38.515693751833382224
| Семена(цвет1)_2 | 11.1479             | 11.5130             | 0.3651              | 11.2935             | 0.1456              | 39.879485072582854013
| Семена(цвет2)_0 | 15.7075             | 16.0418             | 0.3343              | 15.8427             | 0.1352              | 40.44271612324259647
| Семена(цвет2)_1 | 11.5080             | 11.8107             | 0.3027              | 11.6276             | 0.1196              | 39.511067063098777668
| Семена(цвет2)_2 | 15.2701             | 15.5897             | 0.3196              | 15.3968             | 0.1267              | 39.643304130162703379
| Семена(сухие)_0 | 11.1781             | 12.4192             | 1.2411              | 11.9057             | 0.7276              | 58.625412940133752316
| Семена(сухие)_1 | 15.7095             | 17.0384             | 1.3289              | 16.4966             | 0.7871              | 59.229437880954172624
| Семена(сухие)_2 | 11.5076             | 12.7774             | 1.2698              | 12.2469             | 0.7393              | 58.221767207434241613
"""

def clean_value(value):
    value_str = str(value).strip()
    if value_str.startswith("stem:[") and value_str.endswith("]"):
        return value_str[6:-1].strip()
    return value_str

data_io = io.StringIO(table_string)
lines = [line.strip() for line in data_io if line.strip()]
data_lines = lines[1:] 

columns = ['ID', 'm_0', 'm_1', 'm_2', 'm_3', 'm_4', 'DW_original']
parsed_data = []

for line in data_lines:
    split_values = line.split('|')
    actual_values = [val.strip() for val in split_values if val.strip()]
    cleaned_row_values = [clean_value(val) for val in actual_values]
    if len(cleaned_row_values) == len(columns):
        parsed_data.append(cleaned_row_values)
    else:
        print(f"Предупреждение: Пропущена строка: {line}. Ожидалось {len(columns)}, получено {len(cleaned_row_values)}: {cleaned_row_values}")

df = pd.DataFrame(parsed_data, columns=columns)

numeric_cols_to_convert = ['m_0', 'm_1', 'm_2', 'm_3', 'm_4', 'DW_original']
for col in numeric_cols_to_convert:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    else:
        print(f"Критическая ошибка: Столбец '{col}' не найден. Выход.")
        exit()

if df.empty:
    print("Ошибка: DataFrame пуст после парсинга. Проверьте входные данные и логику парсинга. Выход.")
    exit()

if df[numeric_cols_to_convert].isnull().any().any():
    print("Предупреждение: Обнаружены NaN после преобразования в числовой тип. Строки с NaN:")
    print(df[df[numeric_cols_to_convert].isnull().any(axis=1)])

def get_group_id(sample_id):
    if not isinstance(sample_id, str): return "unknown_group"
    normalized_id = sample_id.replace("_{", "_").replace("}", "")
    parts_dot = normalized_id.rsplit('.', 1)
    if len(parts_dot) == 2 and parts_dot[1].isdigit(): return parts_dot[0]
    parts_underscore = normalized_id.rsplit('_', 1)
    if len(parts_underscore) == 2 and parts_underscore[1].isdigit(): return parts_underscore[0]
    return normalized_id 

if 'ID' in df.columns:
    df['Group'] = df['ID'].apply(get_group_id)
else:
    print("Ошибка: Столбец 'ID' не найден. Невозможно создать столбец 'Group'. Выход.")
    exit()

dw_check_successful = False
if 'm_4' in df.columns and 'm_2' in df.columns and 'DW_original' in df.columns:
    df['DW_calculated'] = np.where(df['m_2'] != 0, (df['m_4'] / df['m_2']) * 100, np.nan)
    comparison_df = df.dropna(subset=['DW_original', 'DW_calculated'])
    if not comparison_df.empty:
        dw_check_passed = np.allclose(comparison_df['DW_original'], comparison_df['DW_calculated'])
        if dw_check_passed:
            print("Проверка DW: OK (соответствуют расчетным m_4 / m_2 * 100).")
            dw_check_successful = True
        else:
            print("Проверка DW: ВНИМАНИЕ! Расхождения в столбце DW.")
    else: 
        print("Проверка DW: Нет данных для сравнения DW_original и DW_calculated.")
else:
    print("Проверка DW: Необходимые столбцы отсутствуют.")

final_table_data = pd.DataFrame()
DECIMAL_PLACES = 4 # Определяем количество знаков после запятой

if 'Group' in df.columns and 'm_2' in df.columns and 'm_4' in df.columns:
    df_for_stats = df.dropna(subset=['m_2', 'm_4'])
    if not df_for_stats.empty:
        mass_stats = df_for_stats.groupby('Group').agg(
            N_replicates=('ID', 'count'),
            mean_m2=('m_2', 'mean'),
            std_m2=('m_2', 'std'),
            mean_m4=('m_4', 'mean'),
            std_m4=('m_4', 'std')
        ).reset_index()

        mass_stats['m_2 (г)'] = mass_stats.apply(lambda row: format_combined_stat_fixed_decimals(row['mean_m2'], row['std_m2'], DECIMAL_PLACES), axis=1)
        mass_stats['m_4 (г)'] = mass_stats.apply(lambda row: format_combined_stat_fixed_decimals(row['mean_m4'], row['std_m4'], DECIMAL_PLACES), axis=1)
        
        final_table_data = mass_stats[['Group', 'N_replicates', 'm_2 (г)', 'm_4 (г)']].copy()
        final_table_data.rename(columns={'N_replicates': 'N'}, inplace=True)

        if 'DW_calculated' in df.columns:
            df_for_dw_stats = df.dropna(subset=['DW_calculated'])
            if not df_for_dw_stats.empty:
                dw_stats_per_group = df_for_dw_stats.groupby('Group').agg(
                    mean_DW=('DW_calculated', 'mean'),
                    std_DW=('DW_calculated', 'std')
                ).reset_index()
                # Для DW оставим 2 знака после запятой, так как это проценты
                dw_stats_per_group['DW (%)'] = dw_stats_per_group.apply(lambda row: format_combined_stat_fixed_decimals(row['mean_DW'], row['std_DW'], 2), axis=1)
                
                if not final_table_data.empty:
                    final_table_data = pd.merge(final_table_data, dw_stats_per_group[['Group', 'DW (%)']], on='Group', how='left')
                else: 
                    final_table_data = dw_stats_per_group[['Group', 'DW (%)']]
            else:
                if not final_table_data.empty:
                     final_table_data['DW (%)'] = "Нет данных"
                print("Статистика для DW: Нет валидных значений 'DW_calculated'.")
        else:
            if not final_table_data.empty:
                final_table_data['DW (%)'] = "Нет данных (расчет невозможен)"
            print("Статистика для DW: Столбец 'DW_calculated' отсутствует.")
    else:
        print("Статистика по массам: Нет валидных данных в 'm_2' или 'm_4'.")
else:
    print("Статистика: Необходимые столбцы ('Group', 'm_2', 'm_4') отсутствуют.")

if not final_table_data.empty:
    print("\n--- Итоговая таблица ---")
    final_table_data.rename(columns={
        'Group': 'Группа',
        'N': 'N (повторностей)',
        'm_2 (г)': 'Масса до сушки (m₂), г',
        'm_4 (г)': 'Масса после сушки (m₄), г',
        'DW (%)': 'Доля сухого веса (DW), %'
    }, inplace=True)
    
    markdown_table = tabulate_function(final_table_data, headers='keys', tablefmt='pipe', showindex=False)
    print(markdown_table)
else:
    print("\nИтоговая таблица не может быть сформирована, так как нет данных для отображения.")

print(f"\nВерсии библиотек: Pandas {pd.__version__}, Numpy {np.__version__}, Tabulate {tabulate_module.__version__}")