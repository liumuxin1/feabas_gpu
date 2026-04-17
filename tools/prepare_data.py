import os
import cv2
import json
import math
import numpy as np
import skimage
import argparse
import shutil
import re
import time
import inspect  # 用于获取函数信息
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from PIL import Image  # 用cv2读取大图可能会失败，所以需要PIL库，具体用法：src_img = np.array(Image.open(src_img_path))
Image.MAX_IMAGE_PIXELS = None
import file_utils
import img_utils

def prepare_data():
    wafer_idx = 20
    txt_file = f"/human_foveal_ro/wafer{wafer_idx}/full_section_list.txt"
    save_overview_imgs_dir = f"/CX/neuro_segment/user/jinhaiqun/out/human_foveal/thumb_guojun/overview_imgs/wafer{wafer_idx}"
    rename_overview_imgs_dir = f"/CX/neuro_segment/user/jinhaiqun/out/human_foveal/thumb_guojun/overview_imgs2/wafer{wafer_idx}"
    os.makedirs(save_overview_imgs_dir, exist_ok=True)
    os.makedirs(rename_overview_imgs_dir, exist_ok=True)
    add_idx = 15066
    with open(txt_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if len(line.strip()) == 0:  # 去除空行
                continue

            replace_src_str = "V:\electronMicroscope\multiSEM_data\Xuetian_lab\human_foveal"
            replace_dst_str = "/human_foveal_ro"
            
            new_line = line.replace(replace_src_str, replace_dst_str).replace("\\", "/").replace("//", "/")
            tmp_sec_path = new_line.strip()
            tmp_sec_dir = os.path.dirname(tmp_sec_path)
            overview_img_path = os.path.join(tmp_sec_dir, os.path.basename(tmp_sec_dir), "overview_imgs", f"{os.path.basename(tmp_sec_path)}.png")

            sec_dir = tmp_sec_path.rsplit("/", 1)[1]
            src_sec_idx = int(sec_dir.split("S")[1].split("R")[0])
            
            dst_sec_idx = src_sec_idx + add_idx
            dst_sec_dir = "{}".format(str(dst_sec_idx).zfill(5))
            dst_line = "ln -s {} ./{}".format(tmp_sec_path, dst_sec_dir)
            print(dst_line)

            if not os.path.isfile(overview_img_path):
                print(f"{overview_img_path} is not exist.")  # 如果有缺失的overview_img，找郭老师补
            else:
                # 拷贝一份保存，并重新创建一个文件夹，里面是正确排序的
                save_overview_img_path = os.path.join(save_overview_imgs_dir, os.path.basename(overview_img_path))
                shutil.copyfile(overview_img_path, save_overview_img_path)
                rename_overview_img_path = os.path.join(rename_overview_imgs_dir, f"{str(dst_sec_idx).zfill(5)}.png")
                shutil.copyfile(save_overview_img_path, rename_overview_img_path)


def gen_section_thumbnail(src_dir, thumb_dir, thumb_rect_dir, scale=1.0):
    """根据原始数据中的full_thumbnail_coordinates.txt数据信息, 只是根据坐标信息将所有图片拼接成一整个切片的缩略图, 以及mfov在切片中的rect图,
       其中src_dir是00001这种的, thumb_dir存储缩略图, thumb_rect_dir存储mfov画框缩略图, scale是缩放系数"""
    print("\033[31m<=== {} {}() start. ===>\033[0m".format(time.strftime("%Y-%m-%d %H:%M:%S"), inspect.currentframe().f_code.co_name))
    src_dir = file_utils.get_abs_dir(src_dir)
    file_utils.create_dir(thumb_dir)
    file_utils.create_dir(thumb_rect_dir)

    base_dir = os.path.basename(src_dir)
    if not base_dir.isdigit():  # 文件夹名称应该是类似00001这种的
        print("Error src_dir name -> {}. It should be like abc/00001.".format(src_dir))
        return

    sec_idx = int(base_dir)

    for file in os.listdir(src_dir):
        abs_file_path = os.path.join(src_dir, file)
        if file == "full_thumbnail_coordinates.txt":  # 这里面直接读取缩略图是为了更快的获取所有tile的拼接结果
            with open(abs_file_path, "r") as f:
                lines = f.readlines()

            img_paths, x_locs, y_locs = [], [], []  # 读取文件中的路径信息、x起点坐标、y起点坐标
            for line in lines:
                str_list = line.split("\t")

                if len(str_list) == 4:
                    img_paths.append(str_list[0].replace("\\", "/"))
                    x_locs.append(float(str_list[1]))
                    y_locs.append(float(str_list[2]))

            x_locs = np.array(x_locs)
            y_locs = np.array(y_locs)
            # 将原点移至(0, 0)位置
            x_locs -= np.min(x_locs)
            y_locs -= np.min(y_locs)

            x_locs = (x_locs * scale).astype(np.uint16)
            y_locs = (y_locs * scale).astype(np.uint16)

    # 读取图像大小，每个图大小一致，所以只需要读第一张图即可
    img_h, img_w = cv2.imread(os.path.join(src_dir, img_paths[0]), 0).shape
    new_img_h, new_img_w = int(img_h * scale), int(img_w * scale)

    total_img = np.ones((np.max(y_locs) + new_img_h, np.max(x_locs) + new_img_w), np.uint8) * 255
    mFov_xy_dict = {}  # 记录图像的mFov索引，以及x, y坐标
    for img_path, x, y in zip(img_paths, x_locs, y_locs):
        img = cv2.imread(os.path.join(src_dir, img_path), 0)
        img = cv2.resize(img, (new_img_w, new_img_h))
        img = ((skimage.exposure.equalize_adapthist(img, kernel_size=(8, 8), clip_limit=0.015)) * 255).astype(np.uint8)
        img = 255 - img
        total_img[y:y + new_img_h, x:x + new_img_w] = img

        mFov_idx = int(os.path.dirname(img_path))
        if mFov_idx not in mFov_xy_dict.keys():
            mFov_xy_dict[mFov_idx] = []

        mFov_xy_dict[mFov_idx].append([x, y])
    cv2.imwrite(os.path.join(thumb_dir, f"{str(sec_idx).zfill(5)}.png"), total_img)

    for mFov_idx, cood in mFov_xy_dict.items():
        cood = np.array(cood)
        xy_min = np.min(cood, 0)
        xy_max = np.max(cood, 0)
        bbox = [xy_min[0], xy_max[0] + new_img_w, xy_min[1], xy_max[1] + new_img_h]
        cv2.rectangle(total_img, (bbox[0], bbox[2]), (bbox[1], bbox[3]), 0, 5)
        cv2.putText(total_img, str(mFov_idx), (int((bbox[0] + bbox[1]) / 2), int((bbox[2] + bbox[3]) / 2)), cv2.FONT_HERSHEY_SIMPLEX, 2, 0, 2)
    cv2.imwrite(os.path.join(thumb_rect_dir, f"{str(sec_idx).zfill(5)}.png"), total_img)
    print("\033[32m<=== {} {}() end. ===>\033[0m".format(time.strftime("%Y-%m-%d %H:%M:%S"), inspect.currentframe().f_code.co_name))


def loop_gen_section_thumbnail(src_dir, thumb_dir, thumb_rect_dir, scale=1.0, process_num=100):
    src_dir = file_utils.get_abs_dir(src_dir)
    thumb_dir = file_utils.create_dir(thumb_dir)
    thumb_rect_dir = file_utils.create_dir(thumb_rect_dir)

    tasks = []
    for sub_dir in os.listdir(src_dir):
        abs_sub_dir = os.path.join(src_dir, sub_dir)
        if sub_dir.isdigit():
            dst_thumb_dir = os.path.join(thumb_dir, os.path.basename(src_dir))
            dst_thumb_rect_dir = os.path.join(thumb_rect_dir, os.path.basename(src_dir))
            tasks.append((abs_sub_dir, dst_thumb_dir, dst_thumb_rect_dir, scale))
            # tasks.append((abs_sub_dir, thumb_dir, thumb_rect_dir, scale))

    if not tasks:
        return

    process_num = min(os.cpu_count(), len(tasks)) if process_num == -1 else min(max(process_num, 1), len(tasks))
    with Pool(processes=process_num) as pool:
        # starmap会将tasks列表中的每个元组解包作为参数传递给decay_flow函数, 它会阻塞直到所有任务完成
        results = pool.starmap(gen_section_thumbnail, tasks)


def main():
    # prepare_data()
    loop_gen_section_thumbnail("/CX/neuro_segment/user/jinhaiqun/em_data/human_foveal/wafer15",
                               "/CX/neuro_segment/user/jinhaiqun/out/human_foveal/thumb",
                               "/CX/neuro_segment/user/jinhaiqun/out/human_foveal/thumb_mfov_rect", scale=0.25)


if __name__ == "__main__":
    main()