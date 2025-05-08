import cipher as ci
import numpy as np
with open('plaintext.txt','r',encoding='gbk') as file:
    content = file.read()
new_content=""
for c in content:
    if('A'<=c<='Z'):
        new_content+=chr(ord(c)-ord('A')+ord('a'))
    else:
        new_content+=c
print(content)
with open('plaintext.txt','w') as file:
    file.write(new_content)
ciphering = ci.cipher(content)
ciphering.cipher()
with open('ciphertext.txt','w') as file:
    file.write(ciphering.ciphered)
np.savetxt("table.txt",ciphering.table,fmt='%d',delimiter=' ')