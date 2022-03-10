def add_round_key(byte_matrix, tmp_key):
    for i in range(0, 16):
        byte_matrix[i % 4][int(i/4)] = byte_matrix[i % 4][int(i/4)] ^ tmp_key[i]
    return byte_matrix


def sub_bytes(byte_matrix, chosen_s_box):
    for i in range(0, len(byte_matrix)):
        for j in range(0, len(byte_matrix[i])):
            # split byte in half
            high, low = divmod(byte_matrix[i][j], 0x10)
            byte_matrix[i][j] = int(chosen_s_box[high][low], 16)
    return byte_matrix


def shift_rows(byte_matrix):
    for i, item in enumerate(byte_matrix):
        for j in range(0, i):
            # delete First item of the list and append it to the last spot
            item.append(item.pop(0))
    return byte_matrix


def shift_rows_inverted(byte_matrix):
    for i, item in enumerate(byte_matrix):
        for j in range(0, i):
            # delete last item and insert it at the beginning
            item.insert(0, item.pop())
    return byte_matrix


def mix_columns(byte_matrix, chosen_sub_matrix):
    tmp = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    # normal matrix multiplication
    for i in range(0, len(byte_matrix)):
        for j in range(0, len(byte_matrix)):
            for k in range(0, len(byte_matrix)):
                tmp[i][j] ^= multiply(chosen_sub_matrix[i][k], byte_matrix[k][j])
    return tmp


def multiply(a, b):
    # multiply function from script
    c = 0
    while a != 0:
        if a % 2 == 1:
            c ^= b
        a = int(a/2)
        b = x_time(b)
    return c


def x_time(a):
    # x_time function from script
    t = a << 1
    if a >= 128:
        t = t ^ 0x1b
    # strip first bit if length > 8
    t &= 0xff
    return t


def convert_to_matrix(tmp_text):
    byte_matrix = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    # convert list into 2d array
    for i, item in enumerate(tmp_text):
        byte_matrix[i % 4][int(i/4)] = item
    return byte_matrix


def convert_to_hex_string(byte_matrix):
    # convert 2d byte array into hex string
    string = ''
    for i in range(0, 16):
        if i != 15:
            string += str(hex(byte_matrix[i % 4][int(i/4)])) + ' '
        else:
            string += str(hex(byte_matrix[i % 4][int(i/4)]))
    return string


def convert_to_number(tmp_text):
    # convert text string into hex array
    tmp_text = tmp_text.split(' ')
    for i in range(0, len(tmp_text)):
        tmp_text[i] = (int(tmp_text[i], 16))
    return tmp_text


def rcon(a):
    # rcon from script
    b = 0b10
    if a == 1:
        return 0x01000000
    elif a == 2:
        return 0x02000000
    else:
        for i in range(0, a-2):
            b = multiply(0b10, b)
    return b * 0x1000000


def rot_word(word):
    for i in range(0, 8):
        # if byte length > 7 first bit would shift to last
        if word > 0x7fffffff:
            word <<= 1
            word -= 0xffffffff
        # if not just shift bits
        else:
            word <<= 1
    return word


def read_s_box(a):
    s_box = []
    if a == True:
        try:
            with open("SBox.txt", "r") as f:
                for line in f.readlines():
                    line = line.strip(",\n")
                    items = line.split(", ")
                    s_box.append(items)
        except FileNotFoundError:
            print(FileNotFoundError)
    else:
        try:
            with open("SBoxInvers.txt", "r") as f:
                for line in f.readlines():
                    line = line.strip(",\n")
                    items = line.split(", ")
                    s_box.append(items)
        except FileNotFoundError:
            print(FileNotFoundError)
    return s_box


def sub_word(word):
    s_box = read_s_box(True)
    b = [0, 0, 0, 0]
    # split whole 32 bit word into 4 bytes like in sub_bytes function
    b[0], b[1] = divmod(word, 0x1000000)
    b[1], b[2] = divmod(b[1], 0x10000)
    b[2], b[3] = divmod(b[2], 0x100)
    word = 0
    for i in range(0, 4):
        # add SBox for every Byte
        high, low = divmod(b[i], 16)
        b[i] = int(s_box[high][low], 16)
        # "append" it to word
        word |= b[i]
        # shift word so next one can get appended
        if i != 3:
            word <<= 8
    return word


def generate_key(tmp_key):
    for i in range(0, 4):
        # make 32 bit Words from byte array
        for j in range(0, 3):
            tmp_key[i] = (tmp_key[i] << 8) | tmp_key.pop(i+1)
    w = []
    # generate key from script
    for i in range(0, 44):
        if i < 4:
            w.append(tmp_key[i])
        elif i >= 4 and i % 4 == 0:
            w.append(w[i-4] ^ rcon(int(i/4)) ^ sub_word(rot_word(w[i-1])))
        else:
            w.append(w[i-4] ^ w[i-1])
    tmp = [0]
    for i in range(0, 44):
        a = 0x1000000
        # append 32 Bit word to tmp
        tmp[i*4] = w.pop(0)
        tmp.append(0)
        for j in range(0, 3):
            # split 32 Bit word into 4 Bytes, append separate
            tmp[i*4+j], tmp[i*4+j+1] = divmod(tmp[i*4+j], a)
            tmp.append(0)
            a /= 0x100
            # remove float conversion
            a = int(a)
    generated_key = []
    for i in range(0, 11):
        # append every 4 arrays to 1 Array (create 2d array of keys)
        generated_key.append(tmp[i*16:i*16+16])
    return generated_key


def encrypt_block(encrypted_text, key):
    s_box = read_s_box(True)
    sub_matrix = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
    while len(encrypted_text) != 16:
        encrypted_text += bytearray(1)
    encrypted_text = convert_to_matrix(encrypted_text)
    encrypted_text = add_round_key(encrypted_text, key[0])
    for i in range(1, 10):
        encrypted_text = sub_bytes(encrypted_text, s_box)
        encrypted_text = shift_rows(encrypted_text)
        encrypted_text = mix_columns(encrypted_text, sub_matrix)
        encrypted_text = add_round_key(encrypted_text, key[i])
    encrypted_text = sub_bytes(encrypted_text, s_box)
    encrypted_text = shift_rows(encrypted_text)
    encrypted_text = add_round_key(encrypted_text, key[10])
    return encrypted_text


def encrypt(tmp_text, tmp_key):
    # create SBox for encryption from File
    s_box = read_s_box(True)
    sub_matrix = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]
    for i in range(0, len(tmp_text)):
        encrypted_text = convert_to_number(tmp_text[i])
        if len(encrypted_text) != 16:
            while len(encrypted_text) != 16:
                encrypted_text.append(0)
        encrypted_text = convert_to_matrix(encrypted_text)
        encrypted_text = add_round_key(encrypted_text, tmp_key[0])
        for j in range(1, 10):
            encrypted_text = sub_bytes(encrypted_text, s_box)
            encrypted_text = shift_rows(encrypted_text)
            encrypted_text = mix_columns(encrypted_text, sub_matrix)
            encrypted_text = add_round_key(encrypted_text, tmp_key[j])
        encrypted_text = sub_bytes(encrypted_text, s_box)
        encrypted_text = shift_rows(encrypted_text)
        encrypted_text = add_round_key(encrypted_text, tmp_key[10])
        tmp_text[i] = convert_to_hex_string(encrypted_text)
    return tmp_text


def decrypt(tmp_text, tmp_key):
    # create SBox for decryption from File
    inverse_s_box = read_s_box(False)
    inverse_sub_matrix = [[0xe, 0xb, 0xd, 0x9], [0x9, 0xe, 0xb, 0xd], [0xd, 0x9, 0xe, 0xb], [0xb, 0xd, 0x9, 0xe]]
    for i in range(0, len(tmp_text)):
        decrypted_text = convert_to_number(tmp_text[i])
        decrypted_text = convert_to_matrix(decrypted_text)
        decrypted_text = add_round_key(decrypted_text, tmp_key[10])
        decrypted_text = shift_rows_inverted(decrypted_text)
        decrypted_text = sub_bytes(decrypted_text, inverse_s_box)
        for j in range(9, 0, -1):
            decrypted_text = add_round_key(decrypted_text, tmp_key[j])
            decrypted_text = mix_columns(decrypted_text, inverse_sub_matrix)
            decrypted_text = shift_rows_inverted(decrypted_text)
            decrypted_text = sub_bytes(decrypted_text, inverse_s_box)
        decrypted_text = add_round_key(decrypted_text, tmp_key[0])
        tmp_text[i] = convert_to_hex_string(decrypted_text)
    return tmp_text


if __name__ == '__main__':
    text = []
    # read Text to encrypt from File
    try:
        with open("text.txt", "r") as f:
            for line in f.readlines():
                line = line.strip("\n")
                text.append(line)
    except FileNotFoundError:
        print(FileNotFoundError)
    # read key to encrypt from File
    try:
        with open("key.txt", "r") as f:
            for i, line in enumerate(f.readlines()):
                if i == 0:
                    line = line.strip("\n")
                    line = convert_to_number(line)
                    key = line
    except FileNotFoundError:
        print(FileNotFoundError)
    # read key to encrypt from File 2
    try:
        with open("key2.txt", "r") as f:
            for i, line in enumerate(f.readlines()):
                if i == 0:
                    line = line.strip("\n")
                    line = convert_to_number(line)
                    key2 = line
    except FileNotFoundError:
        print(FileNotFoundError)
    key = generate_key(key)
    key2 = generate_key(key2)
    print(text)
    encrypt(text, key)
    print(text)
    decrypt(text, key)
    print(text)
    encrypt(text, key2)
    print(text)
    decrypt(text, key2)
    print(text)
