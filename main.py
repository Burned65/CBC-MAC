import random
import AES


def cbc_mac(key, text):
    iv = 0


def ccm_mode(key, nonce, text):
    ctr = nonce << 64
    t = []
    for i in range(len(text) + 1):
        t.append(ctr + i % (2**len(text)))
    y = []
    for i in range(1, len(text) + 1):
        y.append(text[i-1] ^ AES.encrypt(key, t[i]))
    tmp = cbc_mac(key, text)
    y_ = t[0] ^ tmp
    y.append(y_)
    return y


if __name__ == '__main__':
    key = "2b 7e 15 16 28 ae d2 a6 ab f7 15 88 09 cf 4f 3c"
    key = AES.convert_to_number(key)
    key = AES.generate_key(key)
    text = ["5c f6 ee 79 2c df 05 e1 ba 2b 63 25 c4 1a 5f 10"]
