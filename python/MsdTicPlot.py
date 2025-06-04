import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

def plot_custom_chromatogram(
    data_string,
    peak_annotations,
    filename="chromatogram.svg",
    x_min=None,
    x_max=None,
    y_scale_type='absolute',  # 'absolute' or 'relative'
    annotation_display_type='both',  # 'text', 'time', 'both'
    y_axis_bottom_padding_factor=0.0,
    hide_top_right_spines=False,
    axes_linewidth=None,
    tick_length=None,
    tick_label_fontsize=None,
    axis_label_fontsize=None,
    plot_title_fontsize=None,
    annotation_fontsize=None 
):
    """
    Generates and saves a chromatogram plot with customizable features.

    Args:
        data_string (str): The raw data string for the chromatogram.
        peak_annotations (dict): A dictionary where keys are peak times (float).
                                 Values can be:
                                 - A string (label only, default offset used).
                                 - A dictionary: {"label": "str", "offset": (x_offset_points, y_offset_points)}
                                   where "label" and "offset" are optional. If "offset" is not
                                   provided, a default is used. If "label" is not provided, it's empty.
        filename (str): The name of the file to save the plot (e.g., "chromatogram.svg").
        x_min (float, optional): Minimum value for the X-axis. Defaults to None (autoscale).
        x_max (float, optional): Maximum value for the X-axis. Defaults to None (autoscale).
        y_scale_type (str): Type of Y-axis scale. 'absolute' or 'relative'.
                            Defaults to 'absolute'.
        annotation_display_type (str): What to display in annotations. 'text', 'time', or 'both'.
                                       Defaults to 'both'.
        y_axis_bottom_padding_factor (float): Factor to determine padding below the minimum data
                                              in view. E.g., 0.05 means 5% of the Y-range in view.
                                              Defaults to 0.0 (no padding).
        hide_top_right_spines (bool): If True, hides the top and right axis spines.
                                      Defaults to False.
        axes_linewidth (float, optional): Linewidth for the axis spines. If None, uses
                                          Matplotlib's default. Also sets major tick width.
                                          Defaults to None.
        tick_length (float, optional): Length of the major tick marks. If None, uses
                                       Matplotlib's default. Defaults to None.
        tick_label_fontsize (float, optional): Font size for axis tick labels. Defaults to None (Matplotlib default).
        axis_label_fontsize (float, optional): Font size for X and Y axis labels/titles. Defaults to None (Matplotlib default).
        plot_title_fontsize (float, optional): Font size for the main plot title. Defaults to None (Matplotlib default).
        annotation_fontsize (float, optional): Font size for peak annotations. Defaults to 8.
    """
    lines = data_string.strip().split('\n')

    try:
        data_start_index = lines.index("----------------") + 1
        time_info_header_index = lines.index("МСД-1 : TIC")
        frequency_line_index = time_info_header_index + 1
        start_time_line_index = time_info_header_index + 2
    except ValueError:
        print("Error: Could not find required headers ('----------------' or 'МСД-1 : TIC') in data_string.")
        return

    if frequency_line_index >= len(lines) or start_time_line_index >= len(lines):
        print("Error: Data string is too short to extract frequency or start time after 'МСД-1 : TIC'.")
        return

    try:
        frequency_points_per_second = float(lines[frequency_line_index])
        actual_start_time_minutes = float(lines[start_time_line_index])
    except ValueError:
        print("Error: Could not parse frequency or start time. Ensure they are valid numbers.")
        return

    raw_intensity_values_str = [line for line in lines[data_start_index:] if line.strip()]
    if not raw_intensity_values_str:
        raw_intensity_values = np.array([])
    else:
        try:
            raw_intensity_values = np.array([float(line) for line in raw_intensity_values_str])
        except ValueError:
            print("Error: Could not parse intensity values. Ensure they are valid numbers.")
            return

    num_points = len(raw_intensity_values)

    fig, ax = plt.subplots(figsize=(15, 7))

    # Apply new axes settings
    if hide_top_right_spines:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    tick_params_to_apply = {}
    if axes_linewidth is not None:
        ax.spines['left'].set_linewidth(axes_linewidth)
        ax.spines['bottom'].set_linewidth(axes_linewidth)
        if not hide_top_right_spines :
            ax.spines['top'].set_linewidth(axes_linewidth)
            ax.spines['right'].set_linewidth(axes_linewidth)
        elif ax.spines['top'].get_visible():
             ax.spines['top'].set_linewidth(axes_linewidth)
        elif ax.spines['right'].get_visible():
             ax.spines['right'].set_linewidth(axes_linewidth)
        tick_params_to_apply['width'] = axes_linewidth
    
    if tick_length is not None:
        tick_params_to_apply['length'] = tick_length
    
    if tick_label_fontsize is not None: # New
        tick_params_to_apply['labelsize'] = tick_label_fontsize

    if tick_params_to_apply:
        ax.tick_params(axis='both', which='major', **tick_params_to_apply)


    ax.set_xlabel("Время (минуты)", fontsize=axis_label_fontsize) # New fontsize
    ax.set_title("Хроматограмма МСД-1 : TIC", fontsize=plot_title_fontsize) # New fontsize
    # ax.grid(True)

    if num_points == 0:
        print("No data points to plot.")
        y_label_empty = "Интенсивность (мВ*с)"
        if y_scale_type == 'relative':
            y_label_empty = "Интенсивность (%)"
            ax.set_ylim(0, 105)
            ax.set_yticks(np.arange(0, 101, 25))
        else:
            ax.set_ylim(0, 1)
        ax.set_ylabel(y_label_empty, fontsize=axis_label_fontsize) # New fontsize
        ax.set_title("Хроматограмма МСД-1 : TIC (Нет данных)", fontsize=plot_title_fontsize) # New fontsize
        
        temp_x_min, temp_x_max = (0,1)
        if x_min is not None: temp_x_min = x_min
        if x_max is not None: temp_x_max = x_max
        if x_min is not None and x_max is not None and x_min > x_max:
            temp_x_min, temp_x_max = x_max, x_min
        elif x_min is not None and x_max is None:
             temp_x_max = temp_x_min + 1
        elif x_max is not None and x_min is None:
             temp_x_min = temp_x_max -1
        
        ax.set_xlim(temp_x_min, temp_x_max)
        
        plt.savefig(filename, format="svg", bbox_inches='tight')
        plt.close(fig)
        print(f"Empty chromatogram saved to {filename}")
        return

    if num_points == 1:
        time_axis = np.array([actual_start_time_minutes])
    elif frequency_points_per_second <= 0:
        print("Error: Frequency must be positive. Using default time axis over 1 minute.")
        time_axis = np.linspace(actual_start_time_minutes, actual_start_time_minutes + 1, num_points)
    else:
        time_interval_per_point_seconds = 1 / frequency_points_per_second
        duration_seconds = (num_points - 1) * time_interval_per_point_seconds
        duration_minutes = duration_seconds / 60
        actual_end_time_minutes = actual_start_time_minutes + duration_minutes
        time_axis = np.linspace(actual_start_time_minutes, actual_end_time_minutes, num_points)

    view_x_min_user, view_x_max_user = x_min, x_max
    if num_points == 1:
        if view_x_min_user is None and view_x_max_user is None:
            view_x_min_final = time_axis[0] - 0.5
            view_x_max_final = time_axis[0] + 0.5
        elif view_x_min_user is None:
            view_x_min_final = min(time_axis[0] - 0.5, view_x_max_user - 1.0)
            view_x_max_final = view_x_max_user
        elif view_x_max_user is None:
            view_x_max_final = max(time_axis[0] + 0.5, view_x_min_user + 1.0)
            view_x_min_final = view_x_min_user
        else:
            view_x_min_final, view_x_max_final = view_x_min_user, view_x_max_user
    else:
        view_x_min_final = view_x_min_user if view_x_min_user is not None else time_axis[0]
        view_x_max_final = view_x_max_user if view_x_max_user is not None else time_axis[-1]

    if view_x_min_final > view_x_max_final: view_x_min_final, view_x_max_final = view_x_max_final, view_x_min_final
    if abs(view_x_min_final - view_x_max_final) < 1e-9 :
        view_x_min_final -= 0.5
        view_x_max_final += 0.5
    
    ax.set_xlim(view_x_min_final, view_x_max_final)
    final_ax_xlim = ax.get_xlim()

    y_label = "Интенсивность (мВ*с)"
    plot_intensity_values = raw_intensity_values.copy()

    if y_scale_type == 'relative':
        y_label = "Интенсивность (%)"
        max_for_normalization = 0.0
        intensities_for_norm_basis = raw_intensity_values
        if x_min is not None or x_max is not None:
            visible_mask_for_norm = (time_axis >= final_ax_xlim[0]) & (time_axis <= final_ax_xlim[1])
            if np.any(visible_mask_for_norm):
                 intensities_for_norm_basis = raw_intensity_values[visible_mask_for_norm]

        if len(intensities_for_norm_basis) > 0 and np.any(intensities_for_norm_basis):
            max_for_normalization = np.max(intensities_for_norm_basis)
        elif num_points > 0 and np.any(raw_intensity_values):
            max_for_normalization = np.max(raw_intensity_values)

        if abs(max_for_normalization) < 1e-9:
            plot_intensity_values = np.zeros_like(raw_intensity_values)
        else:
            plot_intensity_values = (raw_intensity_values / max_for_normalization) * 100
    
    ax.set_ylabel(y_label, fontsize=axis_label_fontsize) # New fontsize
    ax.plot(time_axis, plot_intensity_values, color='blue')

    visible_data_mask = (time_axis >= final_ax_xlim[0]) & (time_axis <= final_ax_xlim[1])
    plot_intensities_in_final_view = plot_intensity_values[visible_data_mask]

    y_min_in_view, y_max_in_view = 0.0, 0.0
    if len(plot_intensities_in_final_view) > 0:
        y_min_in_view = np.min(plot_intensities_in_final_view)
        y_max_in_view = np.max(plot_intensities_in_final_view)
    
    current_y_range_in_view = y_max_in_view - y_min_in_view

    if y_scale_type == 'relative':
        if (len(plot_intensities_in_final_view) == 0 and num_points > 0) or \
           (len(plot_intensities_in_final_view) > 0 and abs(y_max_in_view) < 1e-6 and abs(y_min_in_view) < 1e-6) :
             final_y_top = 105
             final_y_bottom = 0
        else:
            bottom_padding_amount_rel = 0.0
            fixed_min_padding_rel = 5.0 
            if y_axis_bottom_padding_factor > 0:
                if abs(current_y_range_in_view) < 1e-9: 
                    temp_padding = abs(y_min_in_view * y_axis_bottom_padding_factor)
                    if abs(temp_padding) < 1e-9: 
                        bottom_padding_amount_rel = fixed_min_padding_rel
                    else:
                        bottom_padding_amount_rel = temp_padding
                else:
                    bottom_padding_amount_rel = current_y_range_in_view * y_axis_bottom_padding_factor
            
            padded_y_min_rel = y_min_in_view - bottom_padding_amount_rel
            final_y_bottom = min(padded_y_min_rel, 0.0)

            annotation_padding_above_max_data = 15.0
            annotation_padding_above_100_tick = 5.0
            required_top_for_data_and_annot = y_max_in_view + annotation_padding_above_max_data
            required_top_for_100_tick = 100.0 + annotation_padding_above_100_tick
            final_y_top = max(required_top_for_data_and_annot, required_top_for_100_tick)

        ax.set_ylim(final_y_bottom, final_y_top)
        ax.set_yticks(np.arange(0, 101, 25))
    else: 
        if len(plot_intensities_in_final_view) > 0 :
            top_padding_amount_abs = 0.0
            if abs(current_y_range_in_view) < 1e-9:
                top_padding_amount_abs = abs(y_max_in_view * 0.15) if abs(y_max_in_view) > 1e-9 else 1.0
            else:
                top_padding_amount_abs = current_y_range_in_view * 0.15
            final_y_top_abs = y_max_in_view + top_padding_amount_abs

            bottom_padding_amount_abs = 0.0
            fixed_min_padding_abs = 0.1 
            if y_axis_bottom_padding_factor > 0:
                if abs(current_y_range_in_view) < 1e-9: 
                    temp_padding = abs(y_min_in_view * y_axis_bottom_padding_factor)
                    if abs(temp_padding) < 1e-9: 
                        bottom_padding_amount_abs = fixed_min_padding_abs
                    else:
                        bottom_padding_amount_abs = temp_padding
                else:
                    bottom_padding_amount_abs = current_y_range_in_view * y_axis_bottom_padding_factor
            final_y_bottom_abs = y_min_in_view - bottom_padding_amount_abs
            
            if abs(final_y_top_abs - final_y_bottom_abs) < 1e-6:
                min_range_val = max(abs(final_y_bottom_abs*0.1), 0.1)
                if final_y_bottom_abs < 0 and abs(final_y_bottom_abs*0.1) < 0.1 : min_range_val = 0.1 
                
                final_y_top_abs = final_y_bottom_abs + min_range_val
                if abs(y_min_in_view) < 1e-9 and abs(y_max_in_view) < 1e-9: 
                     final_y_top_abs = max(final_y_top_abs, 1.0) 
                     if y_axis_bottom_padding_factor == 0: 
                         final_y_bottom_abs = 0.0

            ax.set_ylim(final_y_bottom_abs, final_y_top_abs)
        else: 
            ax.set_ylim(0, 1) 
        ax.yaxis.set_major_locator(MaxNLocator(nbins='auto', prune='both', min_n_ticks=4))

    # Determine annotation fontsize (use default if not provided)
    current_annotation_fontsize = annotation_fontsize if annotation_fontsize is not None else 8

    default_annotation_offset = (0, 15)
    for peak_time, annotation_info_or_label in peak_annotations.items():
        if not (final_ax_xlim[0] <= peak_time <= final_ax_xlim[1]):
            continue 
        
        idx = np.argmin(np.abs(time_axis - peak_time))
        peak_plot_intensity = plot_intensity_values[idx]

        current_xytext_offset = default_annotation_offset
        peak_label_str = ""
        
        if isinstance(annotation_info_or_label, dict):
            peak_label_str = annotation_info_or_label.get("label", "")
            custom_offset = annotation_info_or_label.get("offset")
            if custom_offset and isinstance(custom_offset, tuple) and len(custom_offset) == 2:
                if isinstance(custom_offset[0], (int, float)) and isinstance(custom_offset[1], (int, float)):
                    current_xytext_offset = custom_offset
        elif isinstance(annotation_info_or_label, str): 
            peak_label_str = annotation_info_or_label

        time_str = f"{peak_time:.2f}"
        final_annotation_text = ""
        if annotation_display_type == 'time': final_annotation_text = time_str
        elif annotation_display_type == 'text': final_annotation_text = peak_label_str
        elif annotation_display_type == 'both':
            final_annotation_text = f"{peak_label_str}\n{time_str}" if peak_label_str else time_str
        else: 
            final_annotation_text = time_str 
        
        if final_annotation_text: 
            ax.annotate(final_annotation_text,
                         (peak_time, peak_plot_intensity),
                         textcoords="offset points", 
                         xytext=current_xytext_offset,
                         ha='center', 
                         va='bottom',
                         fontsize=current_annotation_fontsize, # New fontsize
                         rotation=90,
                         arrowprops=dict(arrowstyle="-", color='red', lw=0.5))

    plt.tight_layout()
    plt.savefig(filename, format="svg", bbox_inches='tight')
    plt.close(fig) 
    print(f"Chromatogram saved to {filename}")

# Usages
data_file_path = "python/MsdTicData.txt"
try:
    with open(data_file_path, 'r', encoding='utf-8') as file:
        data_string = file.read()
except FileNotFoundError:
    print(f"Ошибка: Файл данных '{data_file_path}' не найден.")
    data_string = "" # Или exit(), или другая обработка ошибки
except Exception as e:
    print(f"Ошибка при чтении файла '{data_file_path}': {e}")
    data_string = "" # Или exit()

peak_annotations_full = {
    13.4390941560981: {"label": "Standard 1"},
    15.3201691631171: {"label": "Standard 2"},
    17.2191591702029: {"label": "Standard 3"},
    19.3976231783316: {"label": "Standard 4"},
    21.980966187971: {"label": "Standard 5"},
    22.418092189602: {"label": "Standard 6", "offset": (0, 75)},
    23.242182192677: {"label": "Standard 7"},
    23.4643281935059: {"label": "Standard 8", "offset": (5, 15)},
    25.3059902003778: {"label": "Standard 9"},
    27.2264782075439: {"label": "Standard 10"},
    27.6600212091616: {"label": "Standard 11", "offset": (0, 5)},
    28.3264592116483: {"label": "Standard 12"},
    31.9381232251248: {"label": "Standard 13"},
    36.1624802408874: {"label": "Standard 14"},
    37.051064244203: {"label": "Standard 15"},
}

peak_annotations_zoom = {
    13.4390941560981: {"label": "Standard 1"},
    15.3201691631171: {"label": "Standard 2"},
    17.2191591702029: {"label": "Standard 3"},
    19.3976231783316: {"label": "Standard 4"},
    21.980966187971: {"label": "Standard 5"},
    22.418092189602: {"label": "Standard 6"},
    23.242182192677: {"label": "Standard 7", "offset": (0, 10)},
    23.4643281935059: {"label": "Standard 8"},
    25.3059902003778: {"label": "Standard 9"},
    27.2264782075439: {"label": "Standard 10"},
    27.6600212091616: {"label": "Standard 11"},
    28.3264592116483: {"label": "Standard 12"},
    31.9381232251248: {"label": "Standard 13"},
    36.1624802408874: {"label": "Standard 14"},
    37.051064244203: {"label": "Standard 15"},
}

plot_custom_chromatogram(
    data_string,
    peak_annotations_full,
    filename="chromatogram_full_absolute.svg",
    y_scale_type='absolute',
    annotation_display_type='both',
    y_axis_bottom_padding_factor=0.01,
    hide_top_right_spines=True,
    axes_linewidth=1.5,
    tick_length=8,
    tick_label_fontsize=12,
    axis_label_fontsize=14,
    plot_title_fontsize=16,
    annotation_fontsize=8,
)

plot_custom_chromatogram(
    data_string,
    peak_annotations_full,
    filename="chromatogram_full_relative.svg",
    y_scale_type='relative',
    annotation_display_type='both',
    y_axis_bottom_padding_factor=0.01,
    hide_top_right_spines=True,
    axes_linewidth=1.5,
    tick_length=8,
    tick_label_fontsize=12,
    axis_label_fontsize=14,
    plot_title_fontsize=16,
    annotation_fontsize=8,
)

plot_custom_chromatogram(
    data_string,
    peak_annotations_zoom,
    filename="chromatogram_zoom_absolute.svg",
    x_min=21.5, x_max=24,
    y_scale_type='absolute',
    annotation_display_type='both',
    y_axis_bottom_padding_factor=0.01,
    hide_top_right_spines=True,
    axes_linewidth=1.5,
    tick_length=8,
    tick_label_fontsize=12,
    axis_label_fontsize=14,
    plot_title_fontsize=16,
    annotation_fontsize=8,
)

plot_custom_chromatogram(
    data_string,
    peak_annotations_zoom,
    filename="chromatogram_zoom_relative.svg",
    x_min=21.5, x_max=24,
    y_scale_type='relative',
    annotation_display_type='both',
    y_axis_bottom_padding_factor=0.01,
    hide_top_right_spines=True,
    axes_linewidth=1.5,
    tick_length=8,
    tick_label_fontsize=12,
    axis_label_fontsize=14,
    plot_title_fontsize=16,
    annotation_fontsize=8,
)

plot_custom_chromatogram(
    data_string,
    peak_annotations_zoom,
    filename="chromatogram_12-30_absolute.svg",
    x_min=12, x_max=30,
    y_scale_type='absolute',
    annotation_display_type='both',
    y_axis_bottom_padding_factor=0.01,
    hide_top_right_spines=True,
    axes_linewidth=1.5,
    tick_length=8,
    tick_label_fontsize=12,
    axis_label_fontsize=14,
    plot_title_fontsize=16,
    annotation_fontsize=8,
)
