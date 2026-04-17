import os
import cv2
import numpy as np
from skimage.transform import rotate
import file_utils

IMAGE_TYPE_LIST = ["jpg", "jpeg", "png", "bmp", "tif", "tiff"]

def convert_img_to_uint8(src_img):
    """将非uint8的图像转成uint8"""
    if src_img.dtype == "uint8":
        return src_img
    else:
        dst_img = src_img - src_img.min()
        dst_img = dst_img / (dst_img.max() - dst_img.min())
        dst_img *= 255
        dst_img = dst_img.astype(np.uint8)
        return dst_img


def get_central_symmetry_img(src_img):
    """根据图像获取其中心对称图像"""
    dst_img = np.zeros(src_img.shape, src_img.dtype)
    for i in range(src_img.shape[0]):
        for j in range(src_img.shape[1]):
            dst_img[i][j] = src_img[src_img.shape[0] - 1 - i][src_img.shape[1] - 1 - j]
    return dst_img


def get_central_symmetry_imgs(src_img_paths, dst_img_paths):
    """根据图像获取其中心对称图像, 其中src_img_paths和dst_img_paths都为列表, 且个数相同, 并且src_img_paths的每一项对应dst_img_paths的每一项"""
    assert len(src_img_paths) == len(dst_img_paths)
    for i in range(len(src_img_paths)):
        if not os.path.isfile(src_img_paths[i]):
            raise Exception("Error! {} is not exist or not a file!".format(src_img_paths[i]))

        file_utils.create_save_dir_from_file(dst_img_paths[i])
        src_img = cv2.imread(src_img_paths[i], cv2.IMREAD_ANYDEPTH)
        dst_img = get_central_symmetry_img(src_img)
        cv2.imwrite(dst_img_paths[i], dst_img)


def img_pixel_value_invert(src_img):
    """图像像素值反转, 比如uint8的图像, 像素为0变为255, 像素255变为0. 暂时只支持uint8和uint16"""
    if src_img.dtype == "uint8":
        max_v = np.power(2, 8) - 1
    elif src_img.dtype == "uint16":
        max_v = np.power(2, 16) - 1
    else:
        raise Exception("Error! Unsupport format {}, only support uint8 and uint16!".format(src_img.dtype))

    dst_img = max_v - src_img
    return dst_img


def rotate_img(src_img, angle, keep_true_size=True, interpolation=cv2.INTER_CUBIC, border_value=255):
    """以图像的中心进行旋转, angle为旋转角度, 逆时针(如果逆时针旋转30度, 则angle为30), keep_true_size默认为True, 表示按照旋转获得的真实尺寸得到旋转后的图, 否则和原图的尺寸保持一致"""
    # (h, w) = src_img.shape[:2]
    # (cx, cy) = (w // 2, h // 2)
    # # 获取原始旋转矩阵
    # M = cv2.getRotationMatrix2D((cx, cy), int(angle), 1.0)  # 第三个参数表示图像旋转后的大小, 这里设为1表示大小与原图大小一致
    # if keep_true_size:
    #     # 计算旋转后图像的边界尺寸
    #     cos = np.abs(M[0, 0])
    #     sin = np.abs(M[0, 1])
    #     new_w = int(h * sin + w * cos)
    #     new_h = int(h * cos + w * sin)

    #     # 调整旋转矩阵的平移量，使图像不裁剪
    #     M[0, 2] += (new_w / 2) - cx
    #     M[1, 2] += (new_h / 2) - cy

    #     dst_img = cv2.warpAffine(src_img, M, (new_w, new_h), flags=interpolation, borderValue=border_value)  # opencv处理不了大图的旋转
    # else:
    #     dst_img = cv2.warpAffine(src_img, M, (w, h), flags=interpolation, borderValue=border_value)

    dst_img = rotate(src_img, angle=angle, resize=keep_true_size, mode='constant', cval=border_value, preserve_range=True, order=3)  # order=3对应双三次插值
    dst_img = dst_img.astype(np.uint8)
    return dst_img


def main():
    src_img_path = "/home/hqjin/Pictures/2022-09-07_14-12.png"
    src_img = cv2.imread(src_img_path, cv2.IMREAD_UNCHANGED)
    dst_img = img_pixel_value_invert(src_img)
    tmp_img_path = file_utils.create_tmp_file_path(src_img_path)
    cv2.imwrite(tmp_img_path, dst_img)    


if __name__ == '__main__':
    main()