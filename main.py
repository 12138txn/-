# main.py
# -*- coding: utf-8 -*-
import tkinter as tk
import gui as gui # Import the new gui module
import logic as logic # Import the new logic module
import math
import string # Needed if cipher.py isn't imported for string.ascii_lowercase

# Standard English letter frequencies (sorted list of tuples) - Unchanged
english_freq_sorted = [
    ('e', 12.70), ('t', 9.06), ('a', 8.17), ('o', 7.51), ('i', 6.97),
    ('n', 6.75), ('s', 6.33), ('h', 6.09), ('r', 5.99), ('d', 4.25),
    ('l', 4.03), ('c', 2.78), ('u', 2.76), ('m', 2.41), ('w', 2.36),
    ('f', 2.23), ('g', 2.02), ('y', 1.97), ('p', 1.93), ('b', 1.29),
    ('v', 0.98), ('k', 0.77), ('j', 0.15), ('x', 0.15), ('q', 0.10),
    ('z', 0.07)
]
# Convert to dict of probabilities (0 to 1) - Unchanged
english_freq_dict = {letter: freq / 100.0 for letter, freq in english_freq_sorted}

# Monogram Log Probabilities - Unchanged
default_log_prob = -15.0
english_mono_log_probs = {}
for letter, prob in english_freq_dict.items():
    if prob > 0:
        english_mono_log_probs[letter] = math.log(prob)
    else:
        english_mono_log_probs[letter] = default_log_prob

# Digram Log Probabilities - Unchanged
english_digram_log_probs = {
    'th': -2.78, 'he': -2.93, 'in': -3.27, 'er': -3.36, 'an': -3.44, 're': -3.58,
    'es': -3.66, 'on': -3.71, 'st': -3.79, 'nt': -3.83, 'en': -3.92, 'at': -3.93,
    'ed': -4.00, 'nd': -4.01, 'to': -4.05, 'or': -4.11, 'ea': -4.18, 'ti': -4.28,
    'ar': -4.32, 'te': -4.35, 'is': -4.50, 'ou': -4.58, 'it': -4.70, 'ha': -4.72,
    'ng': -4.77, 'as': -4.80, 'et': -4.95, 'se': -5.00, 'le': -5.10, 'of': -5.12,
    # Add more if needed, or load from a file
}

# Common Trigrams (as a set for efficient lookup) - Unchanged
common_trigrams = {
    "the", "and", "ing", "her", "ere", "ent", "tha", "nth", "was", "eth",
    "for", "dth", "hat", "she", "ion", "tio", "ter", "est", "ers", "ati",
    "his", "oft", "sth", "ith", "ver", "all", "ess", "not", "are", "but",
    # Add more if needed, or load from a file
}

# --- Define Word List File Paths ---
# IMPORTANT: Make sure these paths are correct relative to where main.py runs,
# or use absolute paths.
WORD_LIST_FILES = {
    'two': 'two_letters_words.txt',
    'three': 'three_letters_words.txt',
    'four': 'four_letters_words.txt'
}


if __name__ == "__main__":
    ciphertext_file = 'ciphertext.txt'
    ciphertext = ""
    # --- File Reading (Identical to original main.py) ---
    try:
        try:
            with open(ciphertext_file, 'r', encoding='utf-8') as file:
                ciphertext = file.read()
        except UnicodeDecodeError:
            print("UTF-8 读取失败, 尝试 GBK 编码...")
            try:
                 with open(ciphertext_file, 'r', encoding='gbk') as file:
                     ciphertext = file.read()
            except Exception as e_inner:
                 print(f"使用 GBK 读取密文文件时出错: {e_inner}")
                 exit()
        except FileNotFoundError:
             print(f"错误: 文件未找到 '{ciphertext_file}'")
             print("请创建该文件并将密文放入其中。")
             # You might want to provide default ciphertext for testing
             # ciphertext = "YMJ QNRJ NX F GTWZLM YMJ WJXY TK YMJ QFBJWX..."
             # if not ciphertext: exit() # Exit if still no ciphertext
             exit() # Exit if file not found
        except Exception as e_outer:
            print(f"读取文件时发生错误: {e_outer}")
            exit()
    except Exception as e:
        print(f"读取密文文件时发生意外错误: {e}")
        exit()

    if not ciphertext:
        print("密文文件为空，无法继续。")
        exit()
    # --- End File Reading ---


    # --- Instantiate Logic and GUI ---
    root = tk.Tk()

    # 1. Create the logic instance with all necessary data, including word lists
    decryption_logic = logic.DecryptionLogic(
        ciphertext=ciphertext,
        standard_freq_sorted=english_freq_sorted,
        standard_freq_dict=english_freq_dict,
        standard_mono_log_probs=english_mono_log_probs,
        standard_digram_log_probs=english_digram_log_probs,
        common_trigrams_set=common_trigrams,
        word_list_files=WORD_LIST_FILES # Pass the dictionary of file paths
    )

    # 2. Create the GUI instance, passing the logic instance to it
    app_gui = gui.DecryptionAppGUI(root, decryption_logic)

    # --- Run the Tkinter main loop ---
    root.mainloop()
