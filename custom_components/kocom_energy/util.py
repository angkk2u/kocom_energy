import struct
import hashlib



def string_to_hex(s):
    return "".join([format(ord(c), "02x") for c in s])


def hex_to_ascii(hex_string):
    bytes_obj = bytes.fromhex(hex_string)
    return bytes_obj.decode("ascii").rstrip("\x00")


def hex_to_decimal(hex_string):
    return int(hex_string, 16)


def hex_to_double(hex_string):
    """ 16진수 문자열을 little-endian 바이트 순서의 double 형식으로 변환 """
    # 16진수 문자열을 little-endian 바이트 순서의 double 형식으로  ( 예: '0102' -> b'\x01\x02' )
    byte_array = bytes.fromhex(hex_string)

    # unpack 메서드는 주어진 바이트 배열을 지정된 형식에 따라 변환
    # "<d"는 little-endian 바이트 순서의 double 형식으로 변환
    return struct.unpack("<d", byte_array)[0]


def md5_hashing(input_string):
    # input_string이 문자열이 아니면 문자열로 변환
    if not isinstance(input_string, str):
        input_string = str(input_string)
    return hashlib.md5(input_string.encode()).hexdigest()


def string_to_padded_hex(input_string, size):
    # input_string이 문자열이 아니면 문자열로 변환
    if not isinstance(input_string, str):
        input_string = str(input_string)
    
    # input_string을 hex로 변환
    hex_string = "".join(hex(ord(c))[2:] for c in input_string)

    # 변환된 hex_string을 왼쪽부터 size만큼 채우고 나머지는 0으로 처리
    padded_hex_string = hex_string.ljust(size, "0")

    return padded_hex_string
