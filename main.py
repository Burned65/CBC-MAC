import random
import AES


def convert_to_int(text):
    for i in range(len(text)):
        text[i] = int.from_bytes(text[i], 'big')
    return text


def split_text(text):
    while len(text) * 8 % 128 != 0:
        text += bytearray(1)
    tmp = []
    for i in range(len(text) // 16):
        tmp.append(text[i*16:i*16+16])
    return tmp


def encrypt_cbc(text, key):
    text = split_text(text)
    iv = 0
    for i, item in enumerate(text):
        item = convert_to_int([item])[0]
        item ^= iv
        text[i] = AES.encrypt_block(split_into_bytes(item), key)
        iv = convert_to_number(text[i])
        text[i] = convert_to_bytearray(text[i])
    return text


def convert_to_number(array):
    tmp = 0
    for items in array:
        for item in items:
            tmp += item
            tmp <<= 8
    tmp >>= 8
    return tmp


def convert_to_bytearray(array):
    tmp = bytearray()
    for items in array:
        for item in items:
            tmp += item.to_bytes(1, 'big')
    return tmp


def split_into_bytes(number):
    tmp = []
    mask = 0xff
    while number != 0:
        tmp.insert(0, number & mask)
        number >>= 8
    return tmp


def ccm_mode(text, key, nonce):
    ctr = nonce << 64
    text = split_text(text)
    encrypted_text = bytearray()
    for i, item in enumerate(text):
        t = (ctr + i) % (2**128)
        t = convert_to_int([t.to_bytes(16, 'big')])[0]
        y = convert_to_number(AES.encrypt_block(split_into_bytes(t), key)) ^ convert_to_int([item])[0]
        encrypted_text += y.to_bytes(16, 'big')
    return encrypted_text


def cbc_mac(text, key):
    return encrypt_cbc(text, key)[-1]


def cbc_mac_ccm(text, key, nonce):
    y = ccm_mode(text, key, nonce)
    tmp = cbc_mac(text, key)
    t_0 = nonce << 64
    y_ = convert_to_int([tmp])[0] ^ t_0
    return y + y_.to_bytes(16, 'big')


def verify_cbc_mac(text, key, hash_value):
    return cbc_mac(text, key) == hash_value


def verify_cbc_mac_ccm(y, key, nonce):
    y_0_to_y_n = y[0:-16]
    y_ = y[-16:]
    x = ccm_mode(y_0_to_y_n, key, nonce)
    print(f"decrypted text is: {x.decode()}")
    t_0 = nonce << 64
    return convert_to_int([y_])[0] == t_0 ^ convert_to_int([cbc_mac(x, key)])[0]


if __name__ == '__main__':
    text = "this is a very long message"
    key = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    key = AES.generate_key(key)
    hash_value = cbc_mac(text.encode(), key)
    print(verify_cbc_mac(text.encode(), key, hash_value))

    nonce = random.randint(0, 2**64-1)
    hash_value = cbc_mac_ccm(text.encode(), key, nonce)
    print(verify_cbc_mac_ccm(hash_value, key, nonce))
