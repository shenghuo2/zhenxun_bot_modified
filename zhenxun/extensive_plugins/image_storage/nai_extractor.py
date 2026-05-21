"""
NAI图片元数据提取模块
从nai_meta.py移植
"""

import gzip
import json
from typing import Union

import numpy as np
from PIL import Image


def byteize(alpha):
    alpha = alpha.T.reshape((-1,))
    alpha = alpha[:(alpha.shape[0] // 8) * 8]
    alpha = np.bitwise_and(alpha, 1)
    alpha = alpha.reshape((-1, 8))
    alpha = np.packbits(alpha, axis=1)
    return alpha


class LSBExtractor:
    def __init__(self, data):
        self.data = byteize(data[..., -1])
        self.pos = 0

    def get_one_byte(self):
        byte = self.data[self.pos]
        self.pos += 1
        return byte

    def get_next_n_bytes(self, n):
        n_bytes = self.data[self.pos:self.pos + n]
        self.pos += n
        return bytearray(n_bytes)

    def read_32bit_integer(self):
        bytes_list = self.get_next_n_bytes(4)
        if len(bytes_list) == 4:
            integer_value = int.from_bytes(bytes_list, byteorder='big')
            return integer_value
        else:
            return None


def extract_image_metadata(image: Union[Image.Image, np.ndarray], get_fec: bool = False) -> dict:
    """
    提取NAI图片的元数据
    
    Args:
        image: PIL Image或numpy数组
        get_fec: 是否获取FEC数据
        
    Returns:
        dict: 元数据字典，包含Description、Source等字段
    """
    if isinstance(image, Image.Image):
        image = np.array(image.convert("RGBA"))

    assert image.shape[-1] == 4 and len(image.shape) == 3, "image format"
    reader = LSBExtractor(image)
    magic = "stealth_pngcomp"
    read_magic = reader.get_next_n_bytes(len(magic)).decode("utf-8")
    assert magic == read_magic, "magic number"
    read_len = reader.read_32bit_integer() // 8
    json_data = reader.get_next_n_bytes(read_len)
    json_data = json.loads(gzip.decompress(json_data).decode("utf-8"))
    if "Comment" in json_data and isinstance(json_data["Comment"], str):
        json_data["Comment"] = json.loads(json_data["Comment"])

    if not get_fec:
        return json_data

    fec_len = reader.read_32bit_integer()
    fec_data = None
    if fec_len != 0xffffffff:
        fec_data = reader.get_next_n_bytes(fec_len // 8)

    return json_data, fec_data
