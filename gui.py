# gui.py
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font, filedialog # Added filedialog
import string
import json # Added json for saving/loading key table
from logic import DecryptionLogic

class DecryptionAppGUI:
    """
    Handles the Graphical User Interface (GUI) for the Decryption App.
    Interacts with DecryptionLogic for state and operations.
    """
    def __init__(self, root, logic_instance: DecryptionLogic):
        self.root = root
        self.logic = logic_instance

        self.ciphertext_display = None
        self.plaintext_display = None
        self.analysis_display = None
        self.suggestion_label = None
        self.apply_button = None
        self.apply_suggestion_button = None
        self.undo_button = None
        self.save_key_button = None # New button
        self.load_key_button = None # New button
        self.key_entries = {}

        self.setup_ui()
        self.refresh_display()

        self.root.bind('<Return>', self.apply_key_changes_event)
        self.root.bind('<Escape>', self.close_window_event)

    def setup_ui(self):
        self.root.title("单表替换密码解密器")
        self.root.geometry("1250x850") # Slightly wider to accommodate new buttons if needed

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=10)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(size=10)
        fixed_font = font.Font(family="Consolas", size=10)

        main_paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(main_paned_window, padding=5)
        main_paned_window.add(left_frame) # Give weight for resizing

        ttk.Label(left_frame, text="密文:").pack(anchor=tk.W)
        self.ciphertext_display = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15, font=fixed_font, relief=tk.SUNKEN, borderwidth=1)
        self.ciphertext_display.insert(tk.END, self.logic.get_ciphertext())
        self.ciphertext_display.config(state=tk.DISABLED)
        self.ciphertext_display.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        ttk.Label(left_frame, text="当前解密文本 (编辑下方替换表后应用):").pack(anchor=tk.W)
        self.plaintext_display = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, height=15, font=fixed_font, relief=tk.SUNKEN, borderwidth=1)
        self.plaintext_display.config(state=tk.DISABLED)
        self.plaintext_display.pack(fill=tk.BOTH, expand=True)
        self.plaintext_display.tag_configure('highlight_current', background='yellow')
        self.plaintext_display.tag_configure('highlight_modified', background='lightgreen')

        right_frame = ttk.Frame(main_paned_window, padding=5)
        main_paned_window.add(right_frame) # Give weight for resizing

        key_frame = ttk.LabelFrame(right_frame, text="替换表 (密文 -> 明文)", padding=5)
        key_frame.pack(fill=tk.X, pady=(0, 5))

        num_cols = 7 # Adjusted for potentially more buttons or wider layout
        validate_cmd = (self.root.register(self.validate_key_input), '%P')
        for i, cipher_char in enumerate(string.ascii_lowercase):
            row, col = divmod(i, num_cols)
            grid_col = col * 2
            ttk.Label(key_frame, text=f"{cipher_char.upper()} ->").grid(row=row, column=grid_col, padx=(5, 0), pady=2, sticky=tk.E)
            entry = ttk.Entry(key_frame, width=3, font=fixed_font, justify=tk.CENTER)
            entry.grid(row=row, column=grid_col + 1, padx=(0, 5), pady=2, sticky=tk.W)
            entry.config(validate="key", validatecommand=validate_cmd)
            entry.bind('<FocusIn>', self.select_all_on_focus)
            self.key_entries[cipher_char] = entry

        analysis_frame = ttk.LabelFrame(right_frame, text="频率分析 & 提示", padding=5)
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.analysis_display = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD, height=10, font=fixed_font, relief=tk.SUNKEN, borderwidth=1)
        self.analysis_display.config(state=tk.DISABLED)
        self.analysis_display.pack(fill=tk.BOTH, expand=True)

        suggestion_frame = ttk.LabelFrame(right_frame, text="替换建议 (基于密文频率+频率匹配+上下文)", padding=5)
        suggestion_frame.pack(fill=tk.X, pady=(0, 5))
        self.suggestion_label = ttk.Label(suggestion_frame, text="加载建议中...", justify=tk.LEFT, font=fixed_font, wraplength=500) # Adjusted wraplength
        self.suggestion_label.pack(anchor=tk.NW, fill=tk.X)

        # Button Frame for actions
        actions_button_frame = ttk.Frame(right_frame, padding=(0, 5, 0, 0))
        actions_button_frame.pack(fill=tk.X, pady=(0,5))

        self.apply_button = ttk.Button(actions_button_frame, text="应用替换表 (Enter)", command=self.apply_key_changes_action)
        self.apply_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        self.apply_suggestion_button = ttk.Button(actions_button_frame, text="应用最佳建议", command=self.apply_top_suggestion_action, state=tk.DISABLED)
        self.apply_suggestion_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 2))

        self.undo_button = ttk.Button(actions_button_frame, text="撤销上次更改", command=self.undo_last_change_action, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # Button Frame for file operations
        file_ops_button_frame = ttk.Frame(right_frame, padding=(0, 5, 0, 0))
        file_ops_button_frame.pack(fill=tk.X, pady=(5,5)) # Added some padding between button rows

        self.save_key_button = ttk.Button(file_ops_button_frame, text="保存替换表", command=self.save_key_table_action)
        self.save_key_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

        self.load_key_button = ttk.Button(file_ops_button_frame, text="读取替换表", command=self.load_key_table_action)
        self.load_key_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))


        legend_frame = ttk.LabelFrame(right_frame, text="颜色图例", padding=5)
        legend_frame.pack(fill=tk.X)
        legend_items = [("未修改", "white"), ("当前修改", "yellow"), ("已修改", "lightgreen")]
        for i, (text, color) in enumerate(legend_items):
            ttk.Label(legend_frame, text=f"{text}: ", width=8).grid(row=0, column=i*2, padx=2, pady=1, sticky=tk.W)
            tk.Frame(legend_frame, width=15, height=15, bg=color, bd=1, relief="solid").grid(row=0, column=i*2+1, padx=2, pady=1)

    def _update_key_table_display(self):
        current_key = self.logic.get_current_key()
        for cipher_char, entry_widget in self.key_entries.items():
            plain_char = current_key.get(cipher_char, cipher_char)
            entry_widget.config(validate="none")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, plain_char.lower())
            entry_widget.config(validate="key")

    def _update_plaintext_display(self):
        decrypted_text = self.logic.get_current_decrypted_text()
        last_changed = self.logic.get_last_changed_chars()
        modified = self.logic.get_modified_set()
        original_ciphertext = self.logic.get_ciphertext()

        self.plaintext_display.config(state=tk.NORMAL)
        self.plaintext_display.delete('1.0', tk.END)

        current_decrypted_index = 0
        for i, cipher_char_original in enumerate(original_ciphertext):
            lower_cipher = cipher_char_original.lower()
            if 'a' <= lower_cipher <= 'z':
                while current_decrypted_index < len(decrypted_text) and not decrypted_text[current_decrypted_index].isalpha():
                    self.plaintext_display.insert(tk.END, decrypted_text[current_decrypted_index])
                    current_decrypted_index += 1
                if current_decrypted_index < len(decrypted_text):
                    plain_display_char = decrypted_text[current_decrypted_index]
                    tag_to_apply = None
                    if lower_cipher in last_changed:
                        tag_to_apply = 'highlight_current'
                    elif lower_cipher in modified:
                        tag_to_apply = 'highlight_modified'
                    self.plaintext_display.insert(tk.END, plain_display_char, tag_to_apply if tag_to_apply else ())
                    current_decrypted_index += 1
            else:
                 self.plaintext_display.insert(tk.END, cipher_char_original)
                 if current_decrypted_index < len(decrypted_text) and decrypted_text[current_decrypted_index] == cipher_char_original:
                     current_decrypted_index += 1
        self.plaintext_display.config(state=tk.DISABLED)

    def _update_analysis_display(self):
        analysis_data = self.logic.get_analysis_data()
        self.analysis_display.config(state=tk.NORMAL)
        self.analysis_display.delete('1.0', tk.END)
        header = "映射字母 | 密文频率(%)  | 标准英文(%) | 标准字母\n"
        header += "-------- | ------------ | ------------- | --------\n"
        display_text = header
        for mapped_plain, cipher_freq_pct, std_freq_pct, std_char in analysis_data:
            line = f" {mapped_plain.upper():<7} | {cipher_freq_pct:>12.2f} | {std_freq_pct:>12.2f} |    {std_char.upper()}   \n"
            display_text += line
        display_text += "\n" + "-"*45 + "\n"
        display_text += "常见解密提示:\n- 单字母词 (常是 'a' 或 'i')\n- 双字母组合 (如 'll', 'ss', 'ee', 'oo')\n- 最常见三字母词 (常是 'the')\n"
        self.analysis_display.insert('1.0', display_text)
        self.analysis_display.config(state=tk.DISABLED)

    def _update_suggestion_display(self):
        suggestions = self.logic.get_suggestions()
        suggestion_text = "最佳建议 (基于密文频率+频率匹配+上下文):\n"
        if suggestions:
            for i, (c_char, p_char, score) in enumerate(suggestions):
                conflicting_cipher = self.logic.check_suggestion_conflict(p_char)
                conflict_indicator = ""
                if conflicting_cipher and conflicting_cipher != c_char:
                    conflict_indicator = f" (!='{p_char.upper()}'已被'{conflicting_cipher.upper()}'确认)"
                suggestion_text += f"{i+1}. {c_char.upper()} -> {p_char.upper()} (评分:{score:.2f}){conflict_indicator}\n"
            self.apply_suggestion_button.config(state=tk.NORMAL)
        else:
            suggestion_text += "无可用建议或未满足计算条件..."
            self.apply_suggestion_button.config(state=tk.DISABLED)
        if self.suggestion_label:
             self.suggestion_label.config(text=suggestion_text.strip())

    def _update_button_states(self):
        can_undo = self.logic.can_undo()
        self.undo_button.config(state=tk.NORMAL if can_undo else tk.DISABLED)

    def refresh_display(self):
        print("Refreshing display...")
        self._update_key_table_display()
        self._update_plaintext_display()
        self._update_analysis_display()
        self._update_suggestion_display()
        self._update_button_states()
        print("Display refresh complete.")

    def apply_key_changes_action(self):
        proposed_key_map = {}
        for cipher_char, entry_widget in self.key_entries.items():
            proposed_key_map[cipher_char] = entry_widget.get().lower()
        success, conflicts = self.logic.apply_key_changes(proposed_key_map)
        if conflicts:
            (c1, p1), (c2, _) = conflicts[0]
            messagebox.showwarning(
                "映射冲突",
                f"警告：密文字母 '{c1.upper()}' 和 '{c2.upper()}' 都映射到了明文 '{p1.upper()}'。\n"
                f"请检查并修正替换表。"
            )
        if success or conflicts:
            self.refresh_display()

    def apply_top_suggestion_action(self):
        suggestions = self.logic.get_suggestions()
        if not suggestions:
            messagebox.showinfo("应用建议", "当前没有可应用的建议。")
            return
        cipher_char, target_plain_char, _ = suggestions[0]
        entry_widget = self.key_entries.get(cipher_char)
        if not entry_widget:
            messagebox.showerror("错误", f"找不到 '{cipher_char.upper()}' 的输入框。")
            return
        entry_widget.config(validate="none")
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, target_plain_char)
        entry_widget.config(validate="key")
        self.apply_key_changes_action()

    def undo_last_change_action(self):
        undone = self.logic.undo_last_change()
        if undone:
            self.refresh_display()
        else:
            messagebox.showinfo("撤销", "没有可恢复的上一步替换表状态。")
            self._update_button_states()

    def save_key_table_action(self):
        """Saves the current substitution key to a file."""
        current_key = self.logic.get_current_key()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="保存替换表"
        )
        if not filepath:
            return # User cancelled

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(current_key, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("保存成功", f"替换表已保存到:\n{filepath}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存替换表时发生错误:\n{e}")

    def load_key_table_action(self):
        """Loads a substitution key from a file."""
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="读取替换表"
        )
        if not filepath:
            return # User cancelled

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_key = json.load(f)

            # Basic validation of the loaded key
            if not isinstance(loaded_key, dict):
                raise ValueError("文件内容不是有效的替换表格式 (应为字典)。")

            valid_key = True
            expected_cipher_chars = set(string.ascii_lowercase)
            loaded_cipher_chars = set(loaded_key.keys())

            if loaded_cipher_chars != expected_cipher_chars:
                 missing = expected_cipher_chars - loaded_cipher_chars
                 extra = loaded_cipher_chars - expected_cipher_chars
                 error_msg = "替换表格式错误:\n"
                 if missing: error_msg += f"  缺少密文字母: {', '.join(sorted(list(missing)))}\n"
                 if extra: error_msg += f"  多出密文字母: {', '.join(sorted(list(extra)))}\n"
                 raise ValueError(error_msg.strip())


            for cipher_char, plain_char in loaded_key.items():
                if not (isinstance(cipher_char, str) and len(cipher_char) == 1 and 'a' <= cipher_char <= 'z'):
                    valid_key = False; break
                if not (isinstance(plain_char, str) and len(plain_char) == 1 and ('a' <= plain_char <= 'z' or plain_char == cipher_char)): # Allow mapping to self
                    # If plain_char is not a letter, it means it's an unmapped (identity) char.
                    # Forcing it to be a letter or identity simplifies.
                    # If we want to allow loading partially filled tables where non-letters mean "clear mapping",
                    # this logic needs adjustment, and logic.py's load_key_from_file needs to handle it.
                    # For now, assume a full a-z -> a-z mapping is in the file.
                    # Or, if a cipher char maps to itself, that's also fine.
                    # What if file has "a": "A" or "a": "aa"? This should be an error.
                    # The logic.load_key_from_file will lowercase it anyway.
                    if not (isinstance(plain_char, str) and len(plain_char) == 1 and plain_char.isalpha()):
                         raise ValueError(f"替换表值 '{plain_char}' (对应密文 '{cipher_char}') 必须是单个小写字母。")
                    loaded_key[cipher_char] = plain_char.lower() # Ensure lowercase

            if not valid_key:
                 raise ValueError("替换表包含无效的字符或格式。密文和明文字母都必须是单个小写字母。")

            # Call logic to update the key
            self.logic.load_key_from_file(loaded_key)
            self.refresh_display() # Update UI with the new key
            messagebox.showinfo("读取成功", f"替换表已从以下文件加载:\n{filepath}")

        except json.JSONDecodeError:
            messagebox.showerror("读取失败", "文件不是有效的 JSON 格式。")
        except ValueError as ve: # Catch our custom validation errors
            messagebox.showerror("读取失败", f"替换表文件内容无效:\n{ve}")
        except Exception as e:
            messagebox.showerror("读取失败", f"读取替换表时发生错误:\n{e}")


    def validate_key_input(self, new_value):
        if not new_value:
            return True
        if len(new_value) == 1 and new_value.isalpha():
            return True
        return False

    def select_all_on_focus(self, event):
        event.widget.select_range(0, tk.END)

    def apply_key_changes_event(self, event=None):
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, ttk.Entry) and focused_widget in self.key_entries.values():
            self.apply_key_changes_action()
            return "break"
        return None

    def close_window_event(self, event=None):
        self.root.destroy()