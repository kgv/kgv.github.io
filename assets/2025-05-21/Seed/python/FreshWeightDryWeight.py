import matplotlib.pyplot as plt
import numpy as np

# Данные из таблицы
seed_ids_str = ["С_1", "С_2", "С_4", "С_6", "С_7", "С_8", "С_9", "С_10"]
# Извлекаем числовые значения из ID для оси X (для позиционирования и как основные метки)
seed_x_positions = np.array([int(s.split('_')[1]) for s in seed_ids_str])
numerical_ids_labels = [str(x) for x in seed_x_positions] # Метки для оси X (числа)

# Даты для аннотаций под числовыми ID
dates_for_annotation = [
    "01 июня", "07 июня", "10 июня", "17 июня",
    "25 июня", "27 июня", "01 июля", "04 июля"
]
dates_to_use = dates_for_annotation

# Данные FW (Fresh Weight)
fw_means = np.array([
    0.0222,
    0.0765,
    0.1227,
    0.2223,
    0.2821,
    0.3988,
    0.5283,
    0.6982,
])
fw_errors = np.array([
    0.0004,
    0.0093,
    0.0056,
    0.0146,
    0.0164,
    0.0571,
    0.0169,
    0.0378,
])

# Данные DW (Dry Weight)
dw_means = np.array([
    0.0035,
    0.0116,
    0.0185,
    0.0352,
    0.0476,
    0.0720,
    0.1182,
    0.1931,
])
dw_errors = np.array([
    0.0001,
    0.0013,
    0.0006,
    0.0020,
    0.0029,
    0.0138,
    0.0110,
    0.0039,
])

# Данные DW% (Dry Weight Percentage)
dw_percent_means = np.array([
    15.74,
    15.18,
    15.08,
    15.85,
    16.86,
    17.99,
    22.36,
    27.69,
])
dw_percent_errors = np.array([
    0.20,
    0.25,
    0.29,
    0.18,
    0.42,
    0.94,
    1.67,
    1.04,
])

# Создание фигуры и первой оси (для FW и DW)
fig, ax1 = plt.subplots(figsize=(14, 9)) # Увеличил высоту для дополнительного пространства внизу

# График FW на первой оси
color_fw = 'royalblue'
line1 = ax1.errorbar(seed_x_positions, fw_means, yerr=fw_errors, fmt='-o', capsize=5, label='FW (Сырая масса, г)', color=color_fw, markersize=7)
ax1.set_ylabel("Масса, г", color='black')
ax1.tick_params(axis='y', labelcolor='black')

# График DW на первой оси
color_dw = 'forestgreen'
line2 = ax1.errorbar(seed_x_positions, dw_means, yerr=dw_errors, fmt='-s', capsize=5, label='DW (Сухая масса, г)', color=color_dw, markersize=7)

# Настройка оси X: сначала метки ID
ax1.set_xticks(seed_x_positions)
ax1.set_xticklabels(numerical_ids_labels) # Устанавливаем числовые ID как основные метки

# Добавляем даты мелким шрифтом под числовыми ID
y_offset_for_dates = -0.065 # Относительно оси X (0) в координатах оси (подобрано)
date_fontsize = 8
date_color = 'dimgray'

for i, pos in enumerate(seed_x_positions):
    ax1.text(pos, y_offset_for_dates, dates_to_use[i],
             transform=ax1.get_xaxis_transform(),
             ha='center', va='top',
             fontsize=date_fontsize, color=date_color)

# Устанавливаем название оси X С ОТСТУПОМ, чтобы оно было ниже дат
xlabel_text = "Размер семени, мм\nДата сбора"
# labelpad - это расстояние в пунктах от тиков (или от текста, если он дальше тиков)
ax1.set_xlabel(xlabel_text, labelpad=35) # Увеличим labelpad, значение подбирается (35-40)

# Создание второй оси Y, разделяющей ту же ось X (для DW%)
ax2 = ax1.twinx()
color_dw_percent = 'orangered'
line3 = ax2.errorbar(seed_x_positions, dw_percent_means, yerr=dw_percent_errors, fmt='-^', capsize=5, label='DW (%)', color=color_dw_percent, markersize=7)
ax2.set_ylabel("Содержание сухой массы, %", color=color_dw_percent)
ax2.tick_params(axis='y', labelcolor=color_dw_percent)

# Добавление общего заголовка
plt.title("Динамика накопления массы и содержания сухой массы в семенах", pad=20)

# Объединение легенд с обеих осей
lines = [line1, line2, line3]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(0.01, 0.98))

# Включение сетки (относится к ax1, но видна на всем графике)
ax1.grid(True, linestyle='--', alpha=0.7)

# Автоматическая коррекция полей.
# fig.tight_layout() # Можно попробовать сначала с ним, но для точного контроля отступов лучше subplots_adjust
# plt.show()

# Ручная настройка отступов для лучшего размещения всех элементов, особенно xlabel под датами
# Увеличиваем нижний отступ, чтобы поместилось название оси ПОД датами
# Эти значения могут потребовать подстройки в зависимости от размера шрифта, длины дат и т.д.
plt.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.20) # bottom увеличен

# Показать график
plt.show()