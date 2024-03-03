import os
import numpy as np
from numba import njit

# Const ordered dithering matrices
# To use decorator numba.njit, matrices must be hard-coded separately
mat2 = np.asarray([[0, 2], [3, 1]])
mat4 = np.asarray([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])
mat8 = np.asarray([[ 0, 32,  8, 40,  2, 34, 10, 42],
                   [48, 16, 56, 24, 50, 18, 58, 26],
                   [12, 44,  4, 36, 14, 46,  6, 38],
                   [60, 28, 52, 20, 62, 30, 54, 22],
                   [ 3, 35, 11, 43,  1, 33,  9, 41],
                   [51, 19, 59, 27, 49, 17, 57, 25],
                   [15, 47,  7, 39, 13, 45,  5, 37],
                   [63, 31, 55, 23, 61, 29, 53, 21]])

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
        file.seek(2, os.SEEK_CUR)
        channel = int.from_bytes(file.read(2), "little")
        assert bmpMarker == b'BM', str.format("Not a BMP file")
        assert fileSize > 0 and width > 0 and height > 0 and channel > 0, str.format("BMP file not valid")
    except AssertionError as e:
        return None, (-1, -1), str(e)
    # read pixel data
    file.seek(24, os.SEEK_CUR)
    data = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height - 1, -1, -1):
        for j in range(width):
            bB = int.from_bytes(file.read(1), "little", signed=False)
            bG = int.from_bytes(file.read(1), "little", signed=False)
            bR = int.from_bytes(file.read(1), "little", signed=False)
            data[i, j] = np.array([bR, bG, bB], dtype=np.uint8)
        # eat up padding 0s in raw data
        for k in range(width % 4):
            r = int.from_bytes(file.read(1), "little", signed=False)
    return data, (width, height), ""

@njit
def cvtGrayscale(data: np.ndarray) -> np.ndarray:
    # returned data will not be 32-aligned
    ret = np.zeros((data.shape[0], data.shape[1], 1), dtype=np.uint8)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ret[i, j, 0] = 0.299 * data[i, j, 0] + 0.587 * data[i, j, 1] + 0.114 * data[i, j, 2]
    return ret

@njit
def cvtAlignedData(data: np.ndarray) -> np.ndarray:
    # dealing with 32-alignment issue, padding (4 - width) % 4 0s
    ret = np.zeros((data.shape[0], data.shape[1] + (4 - data.shape[1]) % 4, 1), dtype=np.uint8)
    ret[0: data.shape[0], 0: data.shape[1]] = data
    return ret

@njit
def cvtOrderedDithering(data: np.ndarray, ditType: int = 0) -> np.ndarray:
    DIM = 2 ** (ditType + 1) # dimension of dithering matrix
    MAX = DIM ** 2 - 1 # maximum value of dithering matrix
    ret = np.zeros(data.shape, dtype=np.uint8)
    match ditType:
        case 0:
            mat = mat2
        case 1:
            mat = mat4
        case _:
            mat = mat8
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            for k in range(data.shape[2]):
                x, y = i % DIM, j % DIM
                ret[i, j, k] = 255 if data[i, j, k] * MAX / 255 > mat[x, y] else 0
    return ret

@njit
def histogram(data: np.ndarray) -> (np.ndarray, int):
    ret = np.zeros((data.shape[2], 256), dtype=np.uint32)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            for k in range(data.shape[2]):
                ret[k, data[i, j, k]] += 1
    return ret, np.sum(ret)

@njit
def colorAdjustment(rawData: np.ndarray,
                    channel: int = 0,
                    inSlider: (int, float, int) = (0, 1.0, 255), # inSlider = (low level, gamma, high level)
                    outSlider: (int, int) = (0, 255), # outSlider = (low level, high level)
                    ) -> np.ndarray:
    ret = np.copy(rawData)
    for i in range(rawData.shape[0]):
        for j in range(rawData.shape[1]):
            if rawData[i, j, channel] <= inSlider[0]:
                pixel = 0
            elif rawData[i, j, channel] >= inSlider[2]:
                pixel = 255
            else:
                pixel = ((rawData[i, j, channel] - inSlider[0]) / (inSlider[2] - inSlider[0])) * 255
            corrected = np.power((pixel / 255), 1 / inSlider[1])
            ret[i, j, channel] = int(corrected * (outSlider[1] - outSlider[0]) + outSlider[0])
    return ret
