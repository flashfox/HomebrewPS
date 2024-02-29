import os
import numpy as np

def readBMP(fileName: str) -> (np.ndarray, (int, int), str):
    # read file and check validity
    try:
        file = open(fileName, 'rb')
    except IOError:
        return None, (0, 0), str.format("File not found")
    try:
        bmpMarker = file.read(2)
        fileSize = int.from_bytes(file.read(4), "little")
        file.seek(12, os.SEEK_CUR)
        width = int.from_bytes(file.read(4), "little")
        height = int.from_bytes(file.read(4), "little")
        assert bmpMarker == b'BM', str.format("Not a BMP file: %s" %fileName)
        assert fileSize > 0 and width > 0 and height > 0, str.format("BMP file not valid: %s" %fileName)
    except AssertionError as e:
        return None, (-1, -1), str(e)

    # read pixel data
    file.seek(28, os.SEEK_CUR)
    data = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height - 1, -1, -1):
        for j in range(width):
            bB = int.from_bytes(file.read(1), "little", signed=False)
            bG = int.from_bytes(file.read(1), "little", signed=False)
            bR = int.from_bytes(file.read(1), "little", signed=False)
            data[i][j] = np.array([bR, bG, bB], dtype=np.uint8)
        # eat up padding 0s in raw data
        for k in range(width % 4):
            r = int.from_bytes(file.read(1), "little", signed=False)

    return data, (width, height), ""

def cvtGrayscale(data: np.ndarray) -> np.ndarray:
    # dealing with 32-alignment issue, padding (4 - width) % 4 0s
    ret = np.zeros((data.shape[0], data.shape[1] + (4 - data.shape[1]) % 4), dtype=np.uint8)
    for i in range(data.shape[0]):
        # for [r, g, b] in row:
            # ret[-1].append(0.299 * r + 0.587 * g + 0.114 * b)
        for j in range(data.shape[1]):
            ret[i][j] = 0.299 * data[i][j][0] + 0.587 * data[i][j][1] + 0.114 * data[i][j][2]

    # return np.asarray(ret, dtype=np.int8)
    return ret