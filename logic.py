# logic.py
# -*- coding: utf-8 -*-
import string
import copy
import math
from collections import Counter
import cipher as ci
import re

class DecryptionLogic:
    def __init__(self, ciphertext, standard_freq_sorted, standard_freq_dict,
                 standard_mono_log_probs, standard_digram_log_probs,
                 common_trigrams_set, word_list_files):
        self.ciphertext = ciphertext
        self.ciphertext_lower = ciphertext.lower()
        self.standard_freq_sorted = standard_freq_sorted
        self.standard_freq_dict = standard_freq_dict
        self.standard_mono_log_probs = standard_mono_log_probs
        self.standard_digram_log_probs = standard_digram_log_probs
        self.common_trigrams_set = common_trigrams_set
        self.default_log_prob = -15.0
        self.invalid_word_penalty = -10.0
        self.valid_word_reward_base = 5.0
        self.single_letter_ia_reward = 6.0
        self.single_letter_other_penalty = -9.0
        self.apostrophe_s_common_letter_reward = 6.0
        self.common_apostrophe_s_letters = {'t', 's', 'd', 'l', 'm', 'v', 'r'}
        self.initial_e_mapping_priority_bonus = 100.0

        self.word_sets = self._load_word_sets(word_list_files)
        self.char_indices = {char: [i for i, c in enumerate(self.ciphertext_lower) if c == char]
                             for char in string.ascii_lowercase}
        self.ciphertext_analyzer = ci.stat(self.ciphertext)
        _cipher_freq_dict_percent = {char: freq for char, freq in self.ciphertext_analyzer.sorted_freq}
        self.ciphertext_freq_dict = {
            chr(ord('a') + i): _cipher_freq_dict_percent.get(chr(ord('a') + i), 0.0) / 100.0
            for i in range(26)
        }
        self.ciphertext_freq_sorted_stable = sorted(
            self.ciphertext_freq_dict.items(), key=lambda item: item[1], reverse=True
        )
        self.most_frequent_cipher_char = None
        if self.ciphertext_freq_sorted_stable:
            self.most_frequent_cipher_char = self.ciphertext_freq_sorted_stable[0][0]

        self.current_key = {c: c for c in string.ascii_lowercase} # Initial key: a->a, b->b, etc.
        self.history = []
        self.modified_from_identity = set()
        self.last_changed_chars = set()
        self.current_suggestions = []
        self.ciphertext_tokens_with_type = []
        raw_tokens = re.split('([a-zA-Z]+)', self.ciphertext_lower)
        for rt in raw_tokens:
            if rt:
                self.ciphertext_tokens_with_type.append((rt, rt.isalpha()))

        self.current_decrypted_text = self._perform_decryption()
        self.decrypted_text_analyzer = ci.stat(self.current_decrypted_text)
        self.calculate_and_store_suggestions()

    def _load_word_sets(self, file_paths):
        word_sets = {2: set(), 3: set(), 4: set()}
        expected_lengths = {'two': 2, 'three': 3, 'four': 4}
        for key, path in file_paths.items():
            length = expected_lengths.get(key)
            if length is None: print(f"Warning: Unknown key '{key}' provided in word_list_files from main.py."); continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if len(word) == length and word.isalpha(): word_sets[length].add(word)
            except FileNotFoundError: print(f"Warning: Word list file not found: {path}. Word scoring for length {length} will be disabled."); word_sets[length] = None
            except Exception as e: print(f"Warning: Error loading word list {path}: {e}. Word scoring for length {length} may be incomplete."); word_sets[length] = None
        return word_sets

    def _perform_decryption_on_word(self, cipher_word, key_map):
        plain_word = ""
        for char in cipher_word: mapped_char = key_map.get(char, char); plain_word += mapped_char
        is_fully_decrypted_alpha = all('a' <= c <= 'z' for c in plain_word)
        return plain_word, is_fully_decrypted_alpha

    def _perform_decryption(self):
        decrypted_list = []
        for char_original in self.ciphertext:
            char_lower = char_original.lower()
            if 'a' <= char_lower <= 'z':
                plain_char_lower = self.current_key.get(char_lower, char_lower)
                display_char = plain_char_lower.upper() if char_original.isupper() else plain_char_lower
                decrypted_list.append(display_char)
            else: decrypted_list.append(char_original)
        return "".join(decrypted_list)

    def _update_modified_set(self):
        self.modified_from_identity.clear()
        for cipher_char, plain_char in self.current_key.items():
            if plain_char != cipher_char: self.modified_from_identity.add(cipher_char)

    def apply_key_changes(self, proposed_key_map):
        new_key = copy.deepcopy(self.current_key); changed_this_operation = set(); has_actual_change = False
        for cipher_char, plain_char_input in proposed_key_map.items():
            current_mapping = self.current_key.get(cipher_char, cipher_char); target_plain_char = current_mapping
            if plain_char_input and plain_char_input.isalpha(): target_plain_char = plain_char_input.lower()
            elif not plain_char_input: target_plain_char = cipher_char # Revert to identity if input is cleared
            if target_plain_char != current_mapping: new_key[cipher_char] = target_plain_char; changed_this_operation.add(cipher_char); has_actual_change = True

        plain_to_cipher_map = {}; conflicts_found = []
        for c, p in new_key.items():
            if p != c and 'a' <= p <= 'z': # Only check for conflicts on non-identity active mappings
                if p in plain_to_cipher_map: conflicts_found.append(((plain_to_cipher_map[p], p), (c, p)))
                else: plain_to_cipher_map[p] = c

        if not has_actual_change and not conflicts_found: # if no change and no new conflict introduced by reverting
            # Check if the proposed map *resolved* a conflict that existed due to identity mappings
            # This is a bit complex, for now, if no actual char mapping changed, assume no critical update needed for history etc.
            # unless a conflict state changed.
            # A simple way: if the new_key is same as current_key and no conflicts, then no real "change" for history.
            # However, the conflict check itself might be the "change" user wants to see.
            # Let's assume apply_key_changes implies an intent that should be recorded if it *results* in a different state or key.
             if new_key == self.current_key: # if key is literally the same and no new conflicts
                 # We still might want to update suggestions if the conflict state shown to user is new
                 if conflicts_found: # If there are conflicts with this new_key (even if same as old)
                     self.calculate_and_store_suggestions() # Recalculate suggestions based on potential new conflict view
                 return False, conflicts_found # No change to key, return existing/new conflicts

        # If there was an actual change or new conflicts are found with the new_key
        self.history.append({'key': copy.deepcopy(self.current_key),'modified': copy.deepcopy(self.modified_from_identity),'last_changed': copy.deepcopy(self.last_changed_chars)})
        self.current_key = new_key
        self.last_changed_chars = changed_this_operation
        self._update_modified_set()
        self.current_decrypted_text = self._perform_decryption()
        self.decrypted_text_analyzer = ci.stat(self.current_decrypted_text)
        self.calculate_and_store_suggestions()
        return True, conflicts_found

    def load_key_from_file(self, loaded_key_map):
        """Loads a key from a file, updates state, and recalculates."""
        # Ensure all chars a-z are in the loaded map, defaulting to identity if somehow missing
        # (GUI validation should prevent this, but good for robustness)
        new_key = {c: c for c in string.ascii_lowercase}
        changed_from_current = set()

        for cipher_char in string.ascii_lowercase:
            # loaded_key_map values should already be lowercase from GUI
            plain_char = loaded_key_map.get(cipher_char, cipher_char) # Default to identity
            new_key[cipher_char] = plain_char
            if self.current_key.get(cipher_char) != plain_char:
                changed_from_current.add(cipher_char)

        # Save current state to history before overwriting
        self.history.append({
            'key': copy.deepcopy(self.current_key),
            'modified': copy.deepcopy(self.modified_from_identity),
            'last_changed': copy.deepcopy(self.last_changed_chars)
        })

        self.current_key = new_key
        # For a loaded key, consider all non-identity mappings as "changed" for highlighting
        # Or, more accurately, what changed *from the previous state*
        # If we want to highlight all differences from identity:
        # self.last_changed_chars = {c for c, p in new_key.items() if c != p}
        # If we want to highlight what changed from the *previous* key:
        self.last_changed_chars = changed_from_current # Or simply all keys in new_key if we treat load as a full reset

        self._update_modified_set() # This will set based on current_key vs identity
        self.current_decrypted_text = self._perform_decryption()
        self.decrypted_text_analyzer = ci.stat(self.current_decrypted_text)
        self.calculate_and_store_suggestions()
        # No conflicts to return here as we assume the loaded key is what the user wants.
        # GUI performs some validation. Further conflict display will happen naturally.

    def undo_last_change(self):
        if not self.history: return False
        prev_state = self.history.pop()
        self.current_key = prev_state['key']
        self.modified_from_identity = prev_state['modified']
        self.last_changed_chars = prev_state['last_changed']
        self.current_decrypted_text = self._perform_decryption()
        self.decrypted_text_analyzer = ci.stat(self.current_decrypted_text)
        self.calculate_and_store_suggestions()
        return True

    def calculate_local_swap_score(self, cipher_char_to_swap, target_plain_char, apply_initial_e_bonus=False):
        occurrences = self.char_indices.get(cipher_char_to_swap, [])
        if not occurrences:
            return -float('inf')

        cipher_weight = 4.0; delta_weight = 2.0; digram_bonus = 0.5; trigram_bonus = 0.8; digram_threshold = -7.0
        cipher_freq = self.ciphertext_freq_dict.get(cipher_char_to_swap, 0.0)
        target_freq = self.standard_freq_dict.get(target_plain_char, 0.0)
        delta_freq = max(0.01, abs(cipher_freq - target_freq))
        log_cipher_freq = math.log(cipher_freq) if cipher_freq > 0 else self.default_log_prob
        base_score = cipher_weight * log_cipher_freq - delta_weight * math.log(delta_freq)

        context_bonus_dt = 0.0
        text_len = len(self.ciphertext_lower)
        for i in occurrences:
             prev_plain = None; prev_is_confirmed = False
             if i > 0:
                 prev_cipher = self.ciphertext_lower[i-1]
                 if 'a' <= prev_cipher <= 'z' and prev_cipher in self.modified_from_identity:
                     prev_plain = self.current_key.get(prev_cipher); prev_is_confirmed = True
                     if prev_plain:
                         digram_prev = prev_plain + target_plain_char
                         if self.standard_digram_log_probs.get(digram_prev, self.default_log_prob) > digram_threshold: context_bonus_dt += digram_bonus
             next_plain = None; next_is_confirmed = False
             if i < text_len - 1:
                 next_cipher = self.ciphertext_lower[i+1]
                 if 'a' <= next_cipher <= 'z' and next_cipher in self.modified_from_identity:
                     next_plain = self.current_key.get(next_cipher); next_is_confirmed = True
                     if next_plain:
                         digram_next = target_plain_char + next_plain
                         if self.standard_digram_log_probs.get(digram_next, self.default_log_prob) > digram_threshold: context_bonus_dt += digram_bonus
             if prev_is_confirmed and next_is_confirmed and prev_plain and next_plain:
                 trigram = prev_plain + target_plain_char + next_plain
                 if trigram in self.common_trigrams_set: context_bonus_dt += trigram_bonus

        word_penalty = 0.0; unique_valid_words_for_reward = set()
        single_letter_bonus = 0.0; apostrophe_s_bonus = 0.0
        temp_key = self.current_key.copy(); temp_key[cipher_char_to_swap] = target_plain_char
        processed_token_indices_for_penalty = set(); processed_token_indices_for_reward_check = set()
        processed_indices_for_single_letter = set(); processed_indices_for_apostrophe = set()

        for token_idx, (token_str, is_alpha_token) in enumerate(self.ciphertext_tokens_with_type):
            if not is_alpha_token: continue
            token_len = len(token_str)
            if token_len in [1, 2, 3, 4] and cipher_char_to_swap in token_str:
                potential_plain_word, is_fully_decrypted_alpha = self._perform_decryption_on_word(token_str, temp_key)
                if is_fully_decrypted_alpha:
                    is_independent_word = True # This logic might need refinement for edge cases
                    # A simple check for independence: not adjacent to another alpha token
                    if token_idx > 0 and self.ciphertext_tokens_with_type[token_idx - 1][1]: is_independent_word = False
                    if token_idx < len(self.ciphertext_tokens_with_type) - 1 and self.ciphertext_tokens_with_type[token_idx + 1][1]: is_independent_word = False
                    # The above independence check is very strict. Might need adjustment.
                    # For now, we assume if a token is alpha, and contains the char, it's relevant.

                    if token_len == 1 and token_str == cipher_char_to_swap: # current token IS the char being swapped
                        if token_idx not in processed_indices_for_single_letter:
                            # Check if it's a standalone word (e.g., surrounded by spaces or punctuation)
                            is_standalone_single = True
                            if token_idx > 0 and self.ciphertext_tokens_with_type[token_idx-1][0].isalpha(): is_standalone_single = False
                            if token_idx < len(self.ciphertext_tokens_with_type) -1 and self.ciphertext_tokens_with_type[token_idx+1][0].isalpha(): is_standalone_single = False

                            if is_standalone_single:
                                if target_plain_char == 'a' or target_plain_char == 'i':
                                    single_letter_bonus += self.single_letter_ia_reward
                                else: single_letter_bonus += self.single_letter_other_penalty
                                processed_indices_for_single_letter.add(token_idx)

                    elif token_len in [2,3,4]:
                        word_list_for_len = self.word_sets.get(token_len)
                        if word_list_for_len is None: continue
                        if token_idx not in processed_token_indices_for_penalty:
                            if potential_plain_word not in word_list_for_len:
                                all_other_confirmed = True
                                for cit in token_str:
                                    if cit == cipher_char_to_swap: continue
                                    if cit not in self.modified_from_identity: all_other_confirmed = False; break
                                if all_other_confirmed:
                                    word_penalty += self.invalid_word_penalty
                                    processed_token_indices_for_penalty.add(token_idx)
                        if potential_plain_word in word_list_for_len:
                            if token_idx not in processed_token_indices_for_reward_check:
                               all_meaningfully_mapped = True
                               for cit in token_str:
                                   if not (cit == cipher_char_to_swap or cit in self.modified_from_identity):
                                       all_meaningfully_mapped = False; break
                               if all_meaningfully_mapped:
                                   unique_valid_words_for_reward.add(potential_plain_word)
                                   processed_token_indices_for_reward_check.add(token_idx)

        for i in occurrences: # Apostrophe check based on original ciphertext_lower structure
            # Look for patterns like <non-alpha>'<cipher_char_to_swap><non-alpha>
            # or <start>'<cipher_char_to_swap><non-alpha>
            # or <non-alpha>'<cipher_char_to_swap><end>
            # A common case is "X's" -> "X'S" where X is a single letter.
            # We are interested if target_plain_char makes sense after an apostrophe.
            # Example: cipher "g" becomes plain "s". If ciphertext has "...N'G...", becomes "...n's..."
            if i > 0 and self.ciphertext_lower[i-1] == "'": # char is preceded by apostrophe
                # And not followed by another letter (e.g. "it's" not "it's'a")
                is_end_of_contraction = True
                if i < len(self.ciphertext_lower) -1 and self.ciphertext_lower[i+1].isalpha():
                    is_end_of_contraction = False

                if is_end_of_contraction and i not in processed_indices_for_apostrophe:
                    if target_plain_char in self.common_apostrophe_s_letters: # 's', 't', 'd', 'l', 'm', 'v', 'r'
                        apostrophe_s_bonus += self.apostrophe_s_common_letter_reward
                    processed_indices_for_apostrophe.add(i)


        word_reward = 0.0
        if len(unique_valid_words_for_reward) >= 2: # Require multiple unique words for stronger signal
            word_reward = len(unique_valid_words_for_reward) * self.valid_word_reward_base

        final_score = (base_score + context_bonus_dt + word_penalty +
                       word_reward + single_letter_bonus + apostrophe_s_bonus)

        if apply_initial_e_bonus:
            final_score += self.initial_e_mapping_priority_bonus

        return final_score

    def suggest_best_swaps(self, num_suggestions=5):
        all_suggestions = []
        alphabet = string.ascii_lowercase

        initial_phase_for_e = False
        if self.most_frequent_cipher_char and not self.modified_from_identity:
            initial_phase_for_e = True
        elif self.most_frequent_cipher_char and \
             self.current_key.get(self.most_frequent_cipher_char) != 'e' and \
             not any(p == 'e' and c in self.modified_from_identity for c, p in self.current_key.items() if c != self.most_frequent_cipher_char):
            initial_phase_for_e = True

        for cipher_char_to_swap in alphabet:
            if cipher_char_to_swap in self.modified_from_identity:
                continue
            for target_plain_char in alphabet:
                if target_plain_char == cipher_char_to_swap:
                    continue
                is_used_by_confirmed_other = False
                for c_other, p_other in self.current_key.items():
                    if p_other == target_plain_char and c_other != cipher_char_to_swap and c_other in self.modified_from_identity:
                        is_used_by_confirmed_other = True; break
                if is_used_by_confirmed_other: continue

                is_used_by_tentative_other_non_identity = False # Check if target_plain is already mapped from another C (not yet confirmed)
                for c_other, p_other in self.current_key.items():
                    # if p_other is the target, AND c_other is not the one we are trying to swap, AND that mapping is NOT an identity mapping
                    if p_other == target_plain_char and c_other != cipher_char_to_swap and p_other != c_other : # and c_other not in self.modified_from_identity (implicit by outer loop):
                         is_used_by_tentative_other_non_identity = True; break
                if is_used_by_tentative_other_non_identity: continue

                apply_e_bonus_for_this_suggestion = False
                if initial_phase_for_e and \
                   cipher_char_to_swap == self.most_frequent_cipher_char and \
                   target_plain_char == 'e':
                    apply_e_bonus_for_this_suggestion = True

                score = self.calculate_local_swap_score(cipher_char_to_swap, target_plain_char,
                                                        apply_initial_e_bonus=apply_e_bonus_for_this_suggestion)
                if score > -float('inf'):
                    all_suggestions.append((cipher_char_to_swap, target_plain_char, score))

        all_suggestions.sort(key=lambda item: item[2], reverse=True)
        return all_suggestions[:num_suggestions]

    def calculate_and_store_suggestions(self):
        if len(self.ciphertext) < 10: self.current_suggestions = []; return # Avoid calc for too short texts
        self.current_suggestions = self.suggest_best_swaps(5)

    def get_ciphertext(self): return self.ciphertext
    def get_current_decrypted_text(self): return self.current_decrypted_text
    def get_current_key(self): return copy.deepcopy(self.current_key)
    def get_analysis_data(self):
        analysis_lines = []
        # Ensure we iterate through cipher chars as they appear in ciphertext freq first
        # then add any missing alphabet chars (that don't appear in ciphertext)
        processed_cipher_chars = set()
        for original_cipher_char, original_cipher_freq_prob in self.ciphertext_freq_sorted_stable:
            mapped_plain_char = self.current_key.get(original_cipher_char, original_cipher_char)
            # Find corresponding standard freq for the mapped_plain_char
            std_char_for_plain = mapped_plain_char # placeholder
            std_freq_for_plain = self.standard_freq_dict.get(mapped_plain_char, 0.0) * 100.0

            # For the "Standard Letter" column, we should show the English letter that has a similar rank.
            # This requires matching rank from ciphertext_freq_sorted_stable to standard_freq_sorted
            rank_idx = self.ciphertext_freq_sorted_stable.index((original_cipher_char, original_cipher_freq_prob))
            std_char_by_rank, std_freq_by_rank = ('?', 0.0)
            if rank_idx < len(self.standard_freq_sorted):
                 std_char_by_rank, std_freq_by_rank = self.standard_freq_sorted[rank_idx]


            original_cipher_freq_percent = original_cipher_freq_prob * 100.0
            analysis_lines.append((mapped_plain_char, original_cipher_freq_percent, std_freq_by_rank, std_char_by_rank))
            processed_cipher_chars.add(original_cipher_char)

        # Add any remaining alphabet letters not in ciphertext (their freq is 0)
        for i in range(26):
            char_alpha = chr(ord('a') + i)
            if char_alpha not in processed_cipher_chars:
                mapped_plain_char = self.current_key.get(char_alpha, char_alpha)
                std_char_by_rank, std_freq_by_rank = ('?', 0.0) # No rank in ciphertext
                # If we are far down the list, standard freq might also be from lower ranks
                # This part might need smarter alignment if we want "Standard Letter" to be meaningful for 0-freq cipher chars
                # For now, just show 0s for cipher side
                if len(processed_cipher_chars) + (i - len(processed_cipher_chars)) < len(self.standard_freq_sorted): # crude index
                    idx = len(processed_cipher_chars) + string.ascii_lowercase.index(char_alpha) - len(processed_cipher_chars)
                    # This indexing is not quite right for alignment.
                    # Simpler: if a cipher char has 0 freq, its "rank" is effectively last.
                    # The "standard letter" column is most useful for high-freq cipher chars.
                    # For 0-freq, perhaps show '?' or the std letter for the mapped plain char.
                    # Let's keep it simple: if not in ciphertext_freq_sorted_stable, its cipher freq is 0.
                    # The std_char and std_freq should correspond to some default low rank.
                    # Find a better way to get the std_char_by_rank and std_freq_by_rank for these 0-freq chars.
                    # For now, using '?' and 0.0 as they don't have a ciphertext rank.
                    # Alternative for 0-freq:
                    # std_char_for_plain = mapped_plain_char
                    # std_freq_for_plain = self.standard_freq_dict.get(mapped_plain_char, 0.0) * 100.0
                    # analysis_lines.append((mapped_plain_char, 0.0, std_freq_for_plain, std_char_for_plain))

                    # The original loop iterates 26 times, so it implicitly handles this by rank.
                    # The current logic above is better as it ties to actual cipher frequencies.
                    # Let's revert to the simpler rank-based display for the analysis table,
                    # as it's about comparing frequency distributions by rank.

        # Reverting to simpler rank-based display for analysis_data as in original:
        analysis_lines_ranked = []
        for i in range(26): # Iterate 26 ranks
            original_cipher_char_at_rank, original_cipher_freq_prob_at_rank = ('?', 0.0)
            if i < len(self.ciphertext_freq_sorted_stable):
                original_cipher_char_at_rank, original_cipher_freq_prob_at_rank = self.ciphertext_freq_sorted_stable[i]

            # This is the actual cipher char that has the i-th highest frequency in the ciphertext
            # We need to show what it's currently MAPPED to.
            mapped_plain_char = self.current_key.get(original_cipher_char_at_rank, original_cipher_char_at_rank)
            if original_cipher_char_at_rank == '?': # if no char at this rank (e.g. very short ciphertext)
                mapped_plain_char = '?'


            std_char_at_rank, std_freq_at_rank = ('?', 0.0)
            if i < len(self.standard_freq_sorted):
                std_char_at_rank, std_freq_at_rank = self.standard_freq_sorted[i]

            original_cipher_freq_percent_at_rank = original_cipher_freq_prob_at_rank * 100.0
            analysis_lines_ranked.append((mapped_plain_char, original_cipher_freq_percent_at_rank, std_freq_at_rank, std_char_at_rank))
        return analysis_lines_ranked # Use this rank-based for consistency with likely intent

    def get_suggestions(self): return list(self.current_suggestions) # Return a copy
    def get_modified_set(self): return set(self.modified_from_identity) # Return a copy
    def get_last_changed_chars(self): return set(self.last_changed_chars) # Return a copy
    def can_undo(self): return bool(self.history)
    def check_suggestion_conflict(self, plain_char_suggestion):
        for c_other, p_other in self.current_key.items():
            if p_other == plain_char_suggestion and c_other in self.modified_from_identity:
                return c_other
        return None