import numpy as np

def process_cell_value(value_str_input):
    """
    Processes a string that might contain a list of numbers.
    Calculates mean and standard deviation if it's a list.
    """
    value_str = value_str_input.strip() # Process the stripped version
    if value_str.startswith('[') and value_str.endswith(']'):
        try:
            numbers_str = value_str[1:-1]
            if not numbers_str.strip(): # Handles "[]" or "[ ]"
                return value_str_input # Return original non-stripped if it was just brackets
            
            numbers = []
            raw_numbers = numbers_str.split(',')
            
            # Check if all parts are empty after split (e.g. from "[,]" or just empty content)
            if not any(s.strip() for s in raw_numbers) and numbers_str: # numbers_str might be " , "
                 return value_str_input


            for x_str in raw_numbers:
                x_str_stripped = x_str.strip()
                # This check is important: if x_str_stripped is empty, float('') will raise ValueError.
                # This can happen with lists like "[1,,2]" or "[1,]"
                if not x_str_stripped:
                    # Or raise an error, or skip. For now, this will lead to ValueError at float()
                    # which is caught below, returning original input. This is a safe default.
                    raise ValueError("Empty string element in list")
                numbers.append(float(x_str_stripped))

            if not numbers: 
                 return value_str_input

            mean = np.mean(numbers)
            
            if len(numbers) < 2:
                std_dev = float('nan') 
            else:
                std_dev = np.std(numbers, ddof=1)

            has_zero = any(x == 0.0 for x in numbers) 
            
            if np.isnan(std_dev):
                std_dev_str = "nan"
            else:
                std_dev_str = f"{std_dev:.4f}"
                
            result = f"{mean:.4f} ±{std_dev_str}"
            if has_zero:
                result += "!"
            return result
        except ValueError: 
            return value_str_input 
        except Exception: 
            return value_str_input 
    else:
        return value_str_input

def process_line(line):
    """
    Processes a single line of a table. If it's a data row with a list,
    it calculates mean/std dev and replaces the list.
    """
    if '|' in line:
        last_pipe_idx = line.rfind('|')
        if last_pipe_idx == -1 or last_pipe_idx == 0 : 
            return line 

        prefix_part = line[:last_pipe_idx+1]
        value_cell_content_original = line[last_pipe_idx+1:]
        
        leading_spaces_count = len(value_cell_content_original) - len(value_cell_content_original.lstrip())
        leading_spaces = " " * leading_spaces_count
        
        value_to_process = value_cell_content_original.strip()
        
        processed_value_payload = process_cell_value(value_to_process)
        
        return f"{prefix_part}{leading_spaces}{processed_value_payload}"
    else:
        return line

def process_all_tables_text(raw_text):
    """
    Processes the entire multi-table text, line by line.
    """
    processed_lines = []
    # Strip leading/trailing newlines from the whole input to avoid empty strings in splitlines if not intended
    for line_content in raw_text.strip().splitlines():
        processed_lines.append(process_line(line_content))
    return "\n".join(processed_lines)

# Provided input data
input_data = """
.16:0
| Семена(размер(1 мм))           | [19.865,20.765,19.015]
| Семена(размер(2 мм))           | [22.699,21.424,22.277]
| Семена(размер(4 мм))           | [17.927,20.210,19.951]
| Семена(размер(6 мм))           | [11.408,13.740,15.191]
| Семена(размер(7 мм))           | [9.084,8.582,9.870]
| Семена(размер(8 мм))           | [7.271,7.354,9.110]
| Семена(размер(9 мм))           | [5.117,6.477,6.760]
| Семена(размер(10 мм))          | [3.894,3.663,4.549,2.958]
| Семена(цвет(зелено-коричневый))| [2.064,2.568,2.212]
| Семена(цвет(коричнево-зеленый))| [2.380,2.510,2.058]
| Семена(финальная стадия)       | [2.033,2.124,2.221]

.18:0
| Семена(размер(1 мм))           | [1.331,1.128,1.349]
| Семена(размер(2 мм))           | [1.531,1.720,1.827]
| Семена(размер(4 мм))           | [1.484,1.329,1.383]
| Семена(размер(6 мм))           | [1.076,0.940,0.830]
| Семена(размер(7 мм))           | [0.685,0.796,0.833]
| Семена(размер(8 мм))           | [0.522,0.624,0.619]
| Семена(размер(9 мм))           | [0.324,0.388,0.401]
| Семена(размер(10 мм))          | [0.167,0.185,0.452,0.143]
| Семена(цвет(зелено-коричневый))| [0.102,0.144,0.149]
| Семена(цвет(коричнево-зеленый))| [0.170,0.163,0.169]
| Семена(финальная стадия)       | [0.073,0.079,0.080]

.18:1-9
| Семена(размер(1 мм))           | [6.030,5.580,5.864]
| Семена(размер(2 мм))           | [6.430,7.007,7.210]
| Семена(размер(4 мм))           | [18.127,12.931,12.854]
| Семена(размер(6 мм))           | [36.171,30.320,26.779]
| Семена(размер(7 мм))           | [33.026,35.777,35.441]
| Семена(размер(8 мм))           | [23.052,26.624,29.236]
| Семена(размер(9 мм))           | [22.600,21.983,23.713]
| Семена(размер(10 мм))          | [24.192,26.223,22.709,20.465]
| Семена(цвет(зелено-коричневый))| [16.069,16.384,14.829]
| Семена(цвет(коричнево-зеленый))| [15.109,14.491,15.351]
| Семена(финальная стадия)       | [15.981,17.030,16.670]

.18:1-9,12
| Семена(размер(1 мм))           | [24.101,26.232,22.691]
| Семена(размер(2 мм))           | [31.658,32.938,34.085]
| Семена(размер(4 мм))           | [32.877,34.330,32.981]
| Семена(размер(6 мм))           | [26.729,28.701,29.621]
| Семена(размер(7 мм))           | [21.774,21.990,24.163]
| Семена(размер(8 мм))           | [19.494,19.311,21.907]
| Семена(размер(9 мм))           | [16.559,17.232,16.429]
| Семена(размер(10 мм))          | [15.216,13.817,16.542,14.583]
| Семена(цвет(зелено-коричневый))| [11.127,13.360,11.606]
| Семена(цвет(коричнево-зеленый))| [13.136,12.659,11.549]
| Семена(финальная стадия)       | [12.881,13.368,12.949]

.18:1-9,12,15
| Семена(размер(1 мм))           | [27.256,28.017,27.073]
| Семена(размер(2 мм))           | [27.556,27.002,25.274]
| Семена(размер(4 мм))           | [21.896,23.522,24.650]
| Семена(размер(6 мм))           | [16.050,18.119,18.550]
| Семена(размер(7 мм))           | [11.396,11.140,12.713]
| Семена(размер(8 мм))           | [8.003,8.969,10.650]
| Семена(размер(9 мм))           | [5.098,6.242,6.289]
| Семена(размер(10 мм))          | [3.580,3.232,3.414,3.047]
| Семена(цвет(зелено-коричневый))| [2.365,2.556,2.413]
| Семена(цвет(коричнево-зеленый))| [2.811,2.710,2.291]
| Семена(финальная стадия)       | [1.721,1.835,1.800]

.20:1-11
| Семена(размер(1 мм))           | [0.167,0.184,0.201]
| Семена(размер(2 мм))           | [0.292,0.317,0.388]
| Семена(размер(4 мм))           | [0.749,0.538,0.587]
| Семена(размер(6 мм))           | [1.488,1.412,0.932]
| Семена(размер(7 мм))           | [7.376,0.152,0.106]
| Семена(размер(8 мм))           | [11.386,10.859,9.439]
| Семена(размер(9 мм))           | [12.633,10.882,10.418]
| Семена(размер(10 мм))          | [11.289,11.928,10.380,11.463]
| Семена(цвет(зелено-коричневый))| [10.696,10.392,9.892]
| Семена(цвет(коричнево-зеленый))| [11.428,9.875,10.229]
| Семена(финальная стадия)       | [10.879,10.802,10.819]

.22:1-13
| Семена(размер(1 мм))           | [0.000,0.035,0.116]
| Семена(размер(2 мм))           | [0.067,0.067,0.089]
| Семена(размер(4 мм))           | [0.087,0.070,0.077]
| Семена(размер(6 мм))           | [0.149,0.208,0.056]
| Семена(размер(7 мм))           | [8.816,12.513,8.111]
| Семена(размер(8 мм))           | [21.844,17.780,12.123]
| Семена(размер(9 мм))           | [27.861,26.748,25.242]
| Семена(размер(10 мм))          | [32.140,32.534,33.401,37.667]
| Семена(цвет(зелено-коричневый))| [44.448,40.341,42.797]
| Семена(цвет(коричнево-зеленый))| [40.411,42.425,42.568]
| Семена(финальная стадия)       | [43.257,41.849,43.211]

.24:1-15
| Семена(размер(1 мм))           | [0.280,0.312,0.356]
| Семена(размер(2 мм))           | [0.558,0.589,0.592]
| Семена(размер(4 мм))           | [0.612,0.633,0.587]
| Семена(размер(6 мм))           | [0.477,0.503,0.378]
| Семена(размер(7 мм))           | [1.799,2.741,2.320]
| Семена(размер(8 мм))           | [4.587,4.087,2.610]
| Семена(размер(9 мм))           | [6.217,6.024,5.866]
| Семена(размер(10 мм))          | [6.417,5.946,6.048,7.272]
| Семена(цвет(зелено-коричневый))| [8.210,9.774,12.134]
| Семена(цвет(коричнево-зеленый))| [10.559,10.469,11.719]
| Семена(финальная стадия)       | [10.218,9.887,9.522]
"""

final_output = process_all_tables_text(input_data)
print(final_output)
