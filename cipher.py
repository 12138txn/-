# cipher.py
import random
from collections import Counter

# --- cipher class (for generating test ciphertext - not used in decryption tool) ---
class cipher:
    def __init__(self, plaintext):
        self.plain = plaintext.lower() # Work with lowercase
        self.table = list(range(0, 26))
        self.ciphered = ""

    def cipher(self):
        # random.seed(824) # Fixed seed for consistent testing if needed
        random.shuffle(self.table)
        print(f"Encryption Key (a->{chr(ord('a')+self.table[0])}, b->...): {self.table}") # Show the key used
        for c in self.plain:
            if 'a' <= c <= 'z':
                self.ciphered += chr(ord('a') + self.table[ord(c) - ord('a')])
            else:
                self.ciphered += c # Keep non-alphabetic characters

# --- decipher class (Original - We will implement decryption differently in window.py) ---
# class decipher:
#     def __init__(self, text, key): # key here is the *encryption* key table
#         self.ciphered = text.lower()
#         self.deciphered = ""
#         self.key = key # encryption key
#         self.detable = list(range(0, 26)) # This will be the decryption map

#     def decipher(self):
#         # Build the inverse map (decryption table)
#         for i in range(26):
#             self.detable[self.key[i]] = i
#         # Decrypt
#         for c in self.ciphered:
#             if 'a' <= c <= 'z':
#                 self.deciphered += chr(ord('a') + self.detable[ord(c) - ord('a')])
#             else:
#                 self.deciphered += c

# --- stat class (Used for frequency analysis) ---
class stat:
    def __init__(self, text):
        self.text = text.lower() # Analyze lowercase
        self.letter_counts = Counter()
        self.letter_freq = {}
        self.total_letters = 0
        self.sorted_freq = [] # List of (letter, frequency) tuples, sorted desc
        self.cal_freq()

    def cal_freq(self):
        for c in self.text:
            if 'a' <= c <= 'z':
                self.letter_counts[c] += 1
                self.total_letters += 1

        if self.total_letters == 0:
            return # Avoid division by zero

        for i in range(26):
            char = chr(ord('a') + i)
            freq = (self.letter_counts[char] / self.total_letters) * 100 if self.total_letters > 0 else 0
            self.letter_freq[char] = freq

        # Sort frequencies
        self.sorted_freq = sorted(self.letter_freq.items(), key=lambda item: item[1], reverse=True)

# --- Example Usage (commented out for the tool) ---
# plaintext = "This is a secret message for testing."
# encrypter = cipher(plaintext)
# encrypter.cipher()
# print(f"Ciphertext: {encrypter.ciphered}")
# print("-" * 20)

# ciphertext_to_solve = encrypter.ciphered
# # We would need encrypter.table to use the old decipher class
# # decrypter = decipher(ciphertext_to_solve, encrypter.table)
# # decrypter.decipher()
# # print(f"Decrypted: {decrypter.deciphered}")

# analyzer = stat(ciphertext_to_solve)
# print("\nCiphertext Frequency Analysis:")
# for char, freq in analyzer.sorted_freq:
#     print(f"{char}: {freq:.2f}%")