# FEABAS

FEABAS（有限元辅助脑组织装配系统）是一个基于有限元分析的 Python 库，用于序列切片电子显微镜连接组学数据集的拼接与对齐。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PyPI](https://img.shields.io/pypi/v/feabas.svg)](https://pypi.org/project/feabas/) [![Python](https://img.shields.io/pypi/pyversions/feabas)](https://www.python.org/downloads/) [![DOI](https://zenodo.org/badge/476492649.svg)](https://doi.org/10.5281/zenodo.17793903)


如果您在使用本包时有任何问题，欢迎在 [GitHub 上提交 issue](https://github.com/YuelongWu/feabas/issues) 或在 [讨论区](https://github.com/YuelongWu/feabas/discussions) 留言。


## 安装

我们使用 Python 3.12.2 进行开发和测试，但代码库应兼容 Python 3.8+。要安装 FEABAS，您可以轻松地从 [PyPI](https://pypi.org/project/feabas/) 下载：

```bash
pip install feabas
```

或者，也可以从 [GitHub 仓库](https://github.com/YuelongWu/feabas) 克隆最新版本并以可编辑模式安装：

```bash
git clone https://github.com/YuelongWu/feabas.git
cd feabas
pip install -e .
```
注意：在 Apple Silicon 上，由于缺少预编译的 wheel，您可能需要从 git 仓库手动安装 [triangle](https://github.com/drufat/triangle)，执行 `pip install git+https://github.com/drufat/triangle.git`。


## 使用方法

### 准备工作

用户首先需要为每个要经过 FEABAS 拼接和对齐流程的数据集创建一个专用**工作目录**。**工作目录**作为单个数据集的自包含环境，定义项目特定的配置，并保存工作流程中生成的中间检查点/结果。在流程开始时，**工作目录**应具有以下文件结构：

```
（工作目录）
 |-- configs
 |   |-- stitching_configs.yaml（可选）
 |   |-- thumbnail_configs.yaml（可选）
 |   |-- alignment_configs.yaml（可选）
 |   |-- material_table.json（可选）
 |
 |-- stitch
 |   |-- stitch_coord
 |       |-- (切片名称_0).txt
 |       |-- (切片名称_1).txt
 |       |-- (切片名称_2).txt
 |       |-- ...
 |
 |-- section_order.txt（可选）
```

在拼接和对齐过程中，FEABAS 会向此工作目录写入许多中间结果。如果再次运行相同的命令，它将跳过有缓存中间结果的部分，仅处理未完成的部分。因此，如果上游发生了变化，用户应仔细清理受影响的缓存结果，以强制代码重新运行。

从版本 3.0.1 开始，除了本地文件系统，工作目录也可以位于 [Google Cloud 存储桶](https://cloud.google.com/storage/docs/creating-buckets) 上。

#### 配置文件
**工作目录**中的 `configs` 文件夹包含项目特定的配置文件，用于覆盖默认设置。如果这些文件不存在，FEABAS 将使用仓库根目录下 `configs` 文件夹中对应的默认配置文件（**不是**工作目录），文件名相同但带有 `default_` 前缀，例如 `default_stitching_configs.yaml`。用户可以复制这些默认配置文件到其**工作目录**的 `configs` 文件夹中，**移除**文件名中的前缀，并根据数据集的具体需求调整文件内容。从版本 3.0.1 开始，用户只需在配置文件中定义部分设置，FEABAS 将自动为未指定的设置从默认文件复制。

#### 拼接坐标文件
`stitch/stitch_coord` 文件夹中的 .txt 文件是用户创建的 [TSV](https://en.wikipedia.org/wiki/Tab-separated_values) 文件，用于指定每个切片的近似瓦片排列。它们是 FEABAS 拼接流水线的输入，通常可以从显微镜的元数据派生。在一个坐标文件中，首先定义一些元数据信息，如图像的根目录（可以是 Google Cloud 存储桶 `gs://{bucket-name}/path/to/your/image/folder`）、像素分辨率（纳米为单位）以及每个图像瓦片的大小（高度在前，宽度在后，像素为单位）。元数据之后是该切片关联的所有图像瓦片的表格，第一列给出每个图像文件相对于根目录的相对路径，第二列和第三列定义图像的 x 和 y 坐标（像素为单位）。一个拼接坐标文本文件的示例如下：

<div><code><ins>s0001.txt</ins></code></div>

```
{ROOT_DIR}	/home/feabas/my_project/raw_data/s0001
{RESOLUTION}	4.0
{TILE_SIZE}	3000	4000
Tile_0001.tif	0	0
Tile_0002.tif	3600	0
Tile_0003.tif	7200	0
Tile_0004.tif	0	2700
Tile_0005.tif	3600	2700
Tile_0006.tif	7200	2700
```

它描述了一个切片，其来自显微镜的原始图像瓦片保存在目录 `/home/feabas/my_project/raw_data/s0001` 下。它包含 6 张图像，高 3000 像素，宽 4000 像素，以 2 行 3 列的网格排列，重叠率为 10%。请注意，对于 TILE_SIZE，第一个是高度，第二个是宽度；而对于图像坐标，x（水平）坐标在前，y（垂直）坐标在后。此外，请确保坐标文件中的字段用水平制表符 `\t` 分隔，当前不支持其他分隔符。通常图像不需要以规则矩形模式排列，图像文件可以有任意名称，只要坐标尽可能准确即可。这使得 FEABAS 也可以用于像 [Zeiss MultiSEM](https://www.zeiss.com/microscopy/us/products/sem-fib-sem/sem/multisem.html) 这样的显微镜。

#### 切片顺序文件（可选）
拼接坐标文本文件的文件名定义了切片的名称。默认情况下，FEABAS 假设最终对齐堆叠中的切片顺序可以通过按切片名称字母排序来重建。如果不是这种情况，用户可以通过在工作目录根目录下提供可选的 `section_order.txt` 文件来定义正确的切片顺序。在该文件中，每行是一个与拼接坐标文件名对应的切片名称（不带 `.txt` 扩展名），它们在文件中的位置定义了它们在对齐堆叠中的位置。

#### 指定 FEABAS 到当前项目
为了让 FEABAS 识别需要处理的数据集，用户需要修改 FEABAS 根目录下 `configs/general_configs.yaml` 文件中的 `working_directory` 字段：

<div><code><ins>feabas/configs/general_configs.yaml</ins></code></div>

```yaml
working_directory: FULL_PATH_TO_THE_WORKING_DIRECTORY_OF_THE_CURRENT_PROJECT
cpu_budget: null
parallel_framework: process

full_resolution: 4
section_thinkness: 30

# 日志配置
...
```

用户也可以在 `general_configs.yaml` 中定义要使用的 CPU 核心数和日志行为。默认情况下，FEABAS 会尝试使用所有可用的 CPU；并将重要信息记录到**工作目录**下的 `logs` 文件夹，同时在 `logs/archive` 文件夹中保留更详细的记录。当拼接坐标文件中未定义图像分辨率时，将使用默认的 `full_resolution` 值。类似地，如果在用户的 `stitching_configs.yaml` 中未定义切片厚度，则将使用 `general_configs.yaml` 中此处定义的厚度。

### 拼接

拼接流水线包含三个不同的步骤：匹配、优化和渲染。用户可以按顺序以不同模式执行主拼接脚本来完成这些步骤。数据集**工作目录**下的 `configs/stitching_configs.yaml` 是对流水线进行更精细控制的地方。例如，用户可以通过操作 YAML 配置文件中的 `num_workers` 和 `cache_size` 字段来平衡速度和内存使用。

#### 匹配

要启动匹配步骤，首先导航到 FEABAS 根目录，然后运行：

```bash
python scripts/stitch_main.py --mode matching
```

该脚本解析 `(work_dir)/stitch/stitch_coord` 文件夹中的坐标文件，检测图像重叠，在检测到的重叠区域中寻找匹配点，最后将结果以 [HDF5](https://www.hdfgroup.org/solutions/hdf5/) 文件格式输出到 `(work_dir)/stitch/match_h5` 文件夹。

如果在匹配步骤中遇到任何错误，FEABAS 仍会尝试保存已有的结果，但使用 `.h5_err` 扩展名代替通常的 `.h5`，同时在日志文件中注册一个错误条目。根据我们的经验，最常见的失败情况是原始图像文件损坏。问题解决后，用户可以再次运行匹配命令，FEABAS 将通过加载 `.h5_err` 文件并仅匹配剩余部分来从中断处继续。但是，如果修改了拼接坐标文件中的瓦片排列，或更改了现有图像的内容，用户应删除 `.h5_err` 文件并重新开始该切片的处理。

#### 优化

要启动优化步骤，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/stitch_main.py --mode optimization
```

它读取 `(work_dir)/stitch/match_h5` 文件夹中的 `.h5` 文件，根据上一步找到的匹配点对每个图像瓦片进行弹性变形，并找到系统的全局最低能量状态。然后将结果转换保存到 `(work_dir)/stitch/tform` 文件夹，也是 HDF5 格式。

#### 渲染

要启动渲染步骤，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/stitch_main.py --mode rendering
```

它读取 `(work_dir)/stitch/tform` 文件夹中的变换文件，并以非重叠的 PNG 瓦片或 [TensorStore](https://google.github.io/tensorstore/python/api/index.html) 数据集（如 Neuroglancer precomputed 格式）渲染拼接后的切片。用户可以通过操作**工作目录** `configs/stitching_configs.yaml` 文件中的 `rendering` 元素来控制渲染过程（如输出瓦片大小、是否使用 [CLAHE](https://en.wikipedia.org/wiki/Adaptive_histogram_equalization#Contrast_Limited_AHE) 等）。默认情况下，FEABAS 会将图像渲染到**工作目录**。如果用户希望保持**工作目录**轻量并将拼接后的图像放到其他位置，可以通过在拼接配置文件中定义目标路径（目前支持本地存储或 [Google Cloud Storage](https://cloud.google.com/storage)）到 `rendering: out_dir` 字段来实现。

### 缩略图对齐

FEABAS 对齐工作流程遵循"从粗到精"的原则，缩略图对齐是最粗的对齐步骤，在拼接后立即进行。缩略图对齐步骤的目标是在较低分辨率下找到相邻切片之间的粗糙对应关系，使后续的精细匹配步骤更加容易。

#### 缩略图生成

要生成拼接图像的缩略图，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/thumbnail_main.py --mode downsample
```

下采样后的缩略图将写入 `(work_dir)/thumbnail_align/thumbnails` 文件夹。用户可以通过**工作目录**中的 `configs/thumbnail_configs.yaml` 控制一些选项；其中 `thumbnail_mip_level` 和 `downsample: thumbnail_highpass` 可能是最重要的。

- `thumbnail_mip_level` 通过指定 [mipmap 级别](https://en.wikipedia.org/wiki/Mipmap) 来控制缩略图的分辨率。当 mipmap 级别增加 1 时，图像下采样因子为 2，mip0 对应全分辨率。缩略图应该足够小，使每个切片能够轻松放入一个图像文件并且计算高效；同时又要足够大，以确保有足够的图像内容来提取特征。根据我们的经验，当下采样后的图像每边大约 500~4000 像素时，缩略图对齐效果最好。用户可以根据切片的尺寸来调整目标缩略图大小。

- `downsample: thumbnail_highpass`：我们观察到，对于某些数据集，在下采样步骤之前应用高通滤波器可以增强缩略图中细胞体的可见性，从而有利于下游的对齐步骤。虽然我们尚未确定哪些数据集最受益于这个小技巧，但根据经验，当处理二次电子图像时将其设置为 true，对于背散射模式拍摄的图像设置为 false。如果 `thumbnail_mip_level` 非常小，最好关闭高通滤波器。

#### 缩略图匹配

要在相邻缩略图之间找到匹配点，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/thumbnail_main.py --mode match
```

它会将包含粗糙匹配点的文件保存到 `(work_dir)/thumbnail_align/matches` 文件夹。

这是整个流水线中最容易出错的步骤，因此我们建议用户在执行此步骤时特别关注 `(work_dir)/logs` 文件夹中生成的警告日志文件。根据我们的经验，最常见的失败模式是显微镜的瞄准不够精确，导致某些相邻切片的 ROI 完全偏移，几乎没有重叠。在这种情况下，用户应计划重新拍摄图像。

作为缩略图匹配失败后的最后手段，FEABAS 允许用户通过 Fiji [BigWarp](https://imagej.net/plugins/bigwarp) 手动定义匹配点。首先，从 `(work_dir)/thumbnail_align/thumbnails` 加载失败的一对缩略图到 [Fiji](https://imagej.net/software/fiji/)，启动 BigWarp，选择第一个切片作为 `moving image`，第二个切片作为 `target image`。手动标记一些对应的点，最好覆盖大部分重叠区域，然后将地标导出为 `(section_name_0)__to__(section_name_1).csv` 文件到 `(work_dir)/thumbnail_align/manual_matches` 文件夹。导航到 FEABAS 根目录，然后运行 `python tools/convert_manual_thumbnail_matches.py`，它将转换手动定义的匹配并将其合并到下游流程中。

默认情况下，缩略图匹配步骤假设缩略图中所有连通区域在与其相邻切片对齐时应具有平滑的变换场。但情况并非总是如此。例如，如果一个切片断裂成多个碎片，所有碎片作为单个 montage 拍摄，则这些断开的部分可能需要非常不同的变换才能重新拼合。FEABAS 允许用户通过修改保存在 `(work_dir)/thumbnail_align/material_masks` 中的掩码文件来解决此问题。每个切片对应一个 PNG 格式的掩码文件，应与其缩略图叠加。在掩码图像中，黑色定义 ROI 内的区域，白色定义 ROI 外的区域。用户可以简单地使用白色标记分裂位点，并将黑色的部分切片断开的"岛屿"。然后 FEABAS 将自动尝试为每个断裂部分找到独特的变换（只要碎片不太碎片化）。更多关于掩码的信息，请参阅本说明文档的"高级主题：对齐中的非平滑变换"部分。

在某些应用中，如果用户只需要使用 FEABAS 对齐单瓦片堆叠（绕过拼接），他们可以将其图像当作缩略图来构建工作目录；如果图像扩展名不是 PNG，需要更改 `(work_dir)\configs\thumbnail_configs.yaml` 中的 `thumbnail_format` 设置以反映这一点。同时，确保在 `(work_dir)/thumbnail_align/material_masks` 中提供掩码文件。每个掩码文件（PNG 格式）应与其对应的图像文件大小相同，其中包含实际数据的区域涂成黑色，ROI 外的区域涂成白色。如果 FEABAS 在带通滤波后的图像上进行匹配，那么通过提供掩码来告诉软件成像区域从哪里开始，这对于确保尖锐的边界不会干扰对齐非常重要。掩码文件还用于为优化步骤生成网格。如果整个图像都包含数据，可以使用与图像大小相同的全黑图像作为材质掩码。

从技术上讲，用户可以从这里直接进入精细对齐步骤。但是，从版本 3.0.1 开始，FEABAS 还提供（并推荐）在缩略图级别执行优化和渲染步骤的选项，分别通过调用：

```bash
python scripts/thumbnail_main.py --mode optimization
```

和

```bash
python scripts/thumbnail_main.py --mode render
```

如果缩略图优化在精细对齐之前完成，得到的变换将应用于全分辨率的精细网格，作为精细对齐的起点。渲染步骤将图像渲染到文件夹 `(work_dir)/thumbnail_align/aligned_thumbnails_{thumbnail_resolution}nm`。


### 精细对齐

精细对齐工作流程在更高分辨率下细化缩略图对齐中找到的匹配点，然后通过求解由有限元方法构建的系统方程来计算对齐整个堆叠的变换。用户可以在**工作目录**的 `configs/alignment_configs.yaml` 中调整与精细对齐工作流程相关的参数。

#### 生成网格

有限元分析的一个关键组成部分是网格生成。FEABAS 允许灵活定义网格几何形状和力学特性，这可以帮助解决连接组数据集中经常遇到的多种伪影，例如断裂切片、褶皱和折叠。更多相关信息请参阅"高级主题：对齐中的非平滑变换"。对于挑战性较小的数据集，用户可以简单地运行：

```bash
python scripts/align_main.py --mode meshing
```

将网格生成到 `(work_dir)/align/mesh` 文件夹，或者直接运行 `matching` 命令，它会在网格尚未生成时自动生成。网格属性（例如定义网格粒度的 `mesh_size`）可以通过 `alignment_configs.yaml` 中的 `meshing` 部分进行控制。

#### 匹配

要启动对齐的精细匹配步骤，旨在从缩略图对齐结果中获得更密集、更准确的匹配点，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/align_main.py --mode matching
```

它读取缩略图对齐中的所有匹配文件，从存储拼接图像的文件夹中找到正确的图像，并在更高分辨率下执行模板匹配。结果将保存到 `(work_dir)/align/matches`。精细匹配步骤的工作分辨率可以通过 `alignment_configs.yaml` 中的 `matching: working_mip_level` 字段来定义。选择工作 mipmap 级别时，宜使图像的 xy 分辨率接近其切片厚度，使其更加各向同性。例如，对于 4nm 全分辨率数据集，对于 30nm 厚的切片可以选择 mip2（16nm）或 mip3（32nm），对于 80nm 切片可以选择 mip4（64nm）。

个人而言，我喜欢在匹配步骤后运行 `tools\visualize_align_match_coverage.py` 来生成匹配位置的可视化（保存到 `(work_dir)/align/matches/match_cover/`）。在这些可视化中，匹配位置用红色（之前的切片）和绿色（之后的切片）通道叠加在每个切片的缩略图上。因此，没有黄色的区域表示缺乏匹配。我认为这对于质量控制很有用。


#### 优化

要运行对齐工作流程的优化步骤，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/align_main.py --mode optimization
```

它加载 `(work_dir)/align/mesh` 文件夹中的网格，按字母顺序排列（或遵循 `(work_dir)/section_order.txt` 如果提供），并使用 `(work_dir)/align/matches` 中的匹配来驱动网格进入对齐。对齐后的网格保存到 `(work_dir)/align/tform` 文件夹。FEABAS 提供两种优化选项：

- "滑动窗口"：它首先在堆叠中选择一个连续的子块（大小和位置由 `alignment_configs.yaml` 中的 `window_size` 和 `start_loc` 字段定义），在该块内进行优化，然后将"窗口"移动到相邻块重复该过程。"窗口"移动前后共享固定数量的切片（由 `alignment_configs.yaml` 中的 `buffer_size` 定义），因此它们被锚定到同一个坐标系。

- "分块"：堆叠首先被分割成小的连续"块"，在每个块内进行优化。然后每个块内对齐的切片被合并为一个"元切片"，并且使用块之间接口处的匹配来对齐这些"元切片"。元切片对齐后，每个"元切片"的变换将应用于其成员切片。最后，进行一些局部松弛以平滑块之间的过渡。

这两个选项之间的选择由 `alignment_configs.yaml` 配置文件中的 `optimization: chunk_settings` 控制。例如，以下是一种可能的设置：

```yaml
# 在 alignment_configs.yaml 中
optimization:
	chunk_settings:
		chunked_to_depth: 1
		default_chunk_size: 16
		junction_width: 0.2
	...
```

- chunked_to_depth：如果设置为 0，将使用"滑动窗口"策略。大于 0 的任何值表示使用"分块"策略。注意"元切片"对齐也可以分块。`chunk_to_depth` 设置基本上定义了多少层"元切片"对齐将被"分块"。例如，如果设置为 2，则原始切片将被分块，它们的元切片也将被"分块"，但第一层元切片的"元切片"将使用"滑动窗口"选项进行对齐。
- default_chunk_size：决定每个块中的切片数量。如果需要对切片的分块方式进行更多控制（例如对于 [ibeam-msem 系统](https://academic.oup.com/mam/article/30/Supplement_1/ozae044.313/7720269)），用户可以在 `(work_dir)/align/chunk_map.json` 创建一个 json 文件，块名称作为其属性名，切片名称列表作为其属性值（例如 {"chunk1": ["section0", "section1", "section2"], "chunk2":["section3", "section4", "section5"], ...}）。
- junction_width：决定在块之间接口处被视为"连接切片"的切片数量（相对于块大小）。连接切片在"分块"对齐的最后一步中再次松弛，以平滑块之间的过渡。

请注意，如果执行优化命令时 `(work_dir)/align/tform` 文件夹中已存在网格，程序将加载这些网格而不是 `(work_dir)/align/mesh` 文件夹中相应切片的网格；并将这些切片视为"锁定"，即不允许移动，仅作为剩余优化过程中的参考。


#### 渲染

FEABAS 提供两种渲染对齐结果的方式：非重叠的 PNG 瓦片（可在 [VAST](https://lichtman.rc.fas.harvard.edu/vast/) 中查看）或 [Neuroglancer](https://github.com/google/neuroglancer) precomputed 格式。

要将对齐后的堆叠渲染为 PNG 瓦片，导航到 FEABAS 根目录，然后运行：

```bash
python scripts/align_main.py --mode rendering
```

同样，用户可以通过 `alignment_configs.yaml` 中的 `rendering` 设置来控制渲染过程的细节。与前面拼接工作流程中的渲染步骤一样，可以通过在配置文件中提供路径到 `rendering: out_dir` 字段来将输出图像定向到**工作目录**以外的其他存储位置。

或者，也可以通过运行将对齐后的堆叠渲染为 Neuroglancer precomputed 卷：

```bash
python scripts/align_main.py --mode tsr
```

渲染过程的细节由 `alignment_configs.yaml` 中的 `tensorstore_rendering` 设置控制。请注意，目前 `rendering` 设置和 `tensorstore_rendering` 是独立的，即更改一个不会影响另一种渲染格式的行为。TensorStore 渲染支持本地存储和 Google Cloud 存储目标。


#### 生成多级渐远图（Mipmaps）

如果用户在最后一步使用了 `--mode render`，也可以运行：

```bash
python scripts/align_main.py --mode downsample
```

为对齐后的堆叠生成多级渐远图，以便在 [VAST](https://lichtman.rc.fas.harvard.edu/vast/) 中可视化。


如果最后一步使用了 `--mode tsr`，则应使用以下命令生成多级渐远图：

```bash
python scripts/align_main.py --mode tsd
```

### 在不同机器上分配工作

大多数 FEABAS 命令（对齐网格生成和优化步骤除外）支持参数 `--start`、`--stop`、`--step` 来将流程限制在数据集的子集上。例如：

```bash
python scripts/stitch_main.py --mode rendering --start 5 --stop 20 --step 3
```

将仅渲染每隔一个的切片，从第 5 张开始到第 20 张结束。

这对于在例如由 [Slurm](https://slurm.schedmd.com/documentation.html) 管理的生产环境中将工作分配到多台机器上非常方便。对于某些步骤，如对齐的 TensorStore 图像进行下采样，建议在一台机器上不带参数再次运行命令，以确保覆盖数据的每个部分。


### TensorStore 相关的内存问题

我注意到在某些机器上，涉及使用 [TensorStore](https://google.github.io/tensorstore/)（例如渲染、下采样、对齐匹配）的 FEABAS 步骤可能导致大量内存使用，这是由内存碎片引起的。如果您使用的是 Linux 机器，可以通过切换到不同的内存分配器（例如 tcmalloc）或降低 `MALLOC_ARENA_MAX` 环境变量来缓解。


### 对抗对齐漂移

FEABAS 使用连接的弹簧网格将变形分散到 Z 轴上。这可以防止其他对齐器中常见的"失控"畸变。然而，该系统在组织变形随机时效果最佳。如果样本存在一致的变化，例如新刀片导致突然的压缩变化，最终堆叠可能仍然显示明显的漂移。

为了减轻持续漂移，用户可以执行迭代参考更新。一旦一轮网格松弛完成，得到的位移可以设置为下一轮的新的"静止状态"。这个过程允许系统逐渐吸收系统性变形，因为初始物理应变的恢复力随着每次迭代而减弱。实际上，这是通过将 .h5 变换文件从 `tform` 文件夹移动到 `mesh` 文件夹来替换现有文件，然后重新启动优化来实现的。对于大型数据集，这个"退火"过程在缩略图对齐步骤期间执行效率最高；校正后的全局几何形状可以被携带过来，为精细对齐提供更好的起始位置。

漂移的次要来源，主要发生在缩略图对齐阶段，源于匹配精度。当缩略图的 XY 分辨率显著低于物理切片厚度时，特征匹配中的微小误差会累积成"随机游走"误差，表现为全局漂移。幸运的是，生物特征通常在低分辨率下表现出局部各向同性：大型结构在 Z 轴上变化较慢，而细尺度纹理则不然。这使得在 Z 轴上相距较远的切片之间的匹配成为可能——在全分辨率下通常无法实现。为了对抗随机游走漂移，FEABAS 支持在缩略图阶段进行长程匹配（例如，匹配 Z 轴上距离相当于 XY 像素大小的切片）。通过将一个切片锚定到多个远距离邻居，可以潜在地减少累积误差。由于全分辨率匹配通常在这种距离上失败，FEABAS 支持单独的匹配列表。只需在您的 `thumbnail_align` 文件夹中提供一个 `match_name.txt` 文件来包含您的远程锚点，在 align 文件夹中为精细尺度相邻切片匹配提供另一个。每个文件中的每一行使用格式 `source__to__target` 定义要匹配的特定对。


### 高级主题：对齐中的非平滑变换

有限元分析的优势在于其处理各种几何形状和力学特性的能力。本包利用这一能力，采用有限元技术对序列切片数据集对齐中的非平滑变形进行建模，从而解决由褶皱和折叠等伪影引起的问题。

此功能接口的核心是两个关键组件：材料属性配置文件和材料掩码。

- 材料属性配置文件：这可以是工作目录中的 `configs/material_table.yaml` 文件，如果不存在则使用 FEABAS 目录中的 `configs/default_material_table.yaml`。提供的 JSON 文件列出了材料、它们的属性以及它们在材料掩码中对应的标签。以下是 `default_material_table.yaml` 中一种名为"wrinkle"的材料的定义示例：

	```yaml
	wrinkle:
		mask_label: 50
		enable_mesh: true
		area_constraint: 0
		render: true
		render_weight: 1.0e-3
		type: MATERIAL_MODEL_ENG
		stiffness_multiplier: 0.4
		poisson_ratio: 0.0
		stiffness_func_factory: feabas.material.asymmetrical_elasticity
		stiffness_func_params:
			strain: [0.0, 0.75, 1.0, 1.01]
			stiffness: [1.5, 1.0, 0.5, 0.0]
	```
	- mask_label：代表此材料在材料掩码图像文件中的标签。例如，这里所有灰度值为 50 的像素将被指定为"wrinkle"材料。标签 0 保留用于默认（正常）材料，255 保留用于空白区域。
	- enable_mesh：是否为材料定义的区域生成网格。如果设置为 false，标记的区域将被排除并视为空。
	- area_constraint：它定义了分配给此材料的区域的网格粒度。它基本上是在进行网格生成步骤时乘以 mesh_size 参数的修改器。因此较小的值给出更细的网格，唯一的例外是 0，它将给出几何约束下最粗糙的网格。
	- render：是否渲染分配给此材料的区域。如果设置为 false，材料在网格松弛步骤中仍会发挥其力学作用，但最终不会被渲染。
	- render_weight：这是一个定义渲染优先级的变量。变换网格后，网格的某些区域可能与同一网格的其他区域发生碰撞。在这种情况下，具有较大"render_weight"值的材料将具有更高的渲染优先级。如果碰撞部分具有相同的"render_weight"，则重叠区域将沿中线拆分，每个碰撞方渲染自己的那一半。
	- type：用于此材料的单元类型。选项有：用于[工程（线性）](https://en.wikipedia.org/wiki/Linear_elasticity)模型的 `"MATERIAL_MODEL_ENG"`，用于 [Saint Venant-Kirchhoff](https://en.wikipedia.org/wiki/Hyperelastic_material#Saint_Venant.E2.80.93Kirchhoff_model) 模型的 `"MATERIAL_MODEL_SVK"`，或用于 [Neo-Hookean](https://en.wikipedia.org/wiki/Neo-Hookean_solid) 模型的 `"MATERIAL_MODEL_NHK"`。实际上，我们发现 `"MATERIAL_MODEL_ENG"` 对于大多数情况已经足够。
	- stiffness_multiplier：应用于刚度矩阵的乘数。较小的值给出更软的材料，较大的值使材料更刚性。默认材料的乘数为 1.0。
	- poisson_ratio：如果 `type` 设置为 `"MATERIAL_MODEL_ENG"`，则使用 [泊松比](https://en.wikipedia.org/wiki/Poisson%27s_ratio)。
	- stiffness_func_factory：用于定义非线性应力/应变关系的函数。它接受在 `stiffness_func_params` 中定义的关键字参数，并返回一个将相对面积变化映射到刚度乘数的函数。例如，这里我实现了 `feabas.material.asymmetrical_elasticity`，它是线性插值器的包装器。通过在 `stiffness_func_params` 中提供应变/刚度采样点，它描述了一种可以自由膨胀（应变 > 1）但难以压缩（应变 < 1）的材料，这正是我们对褶皱建模所需要的。如果设置为 null，则材料刚度不是其面积变化的函数。

- 材料掩码：对于每个存在需要非平滑变形场进行对齐的伪影的切片，应提供一个材料掩码。材料掩码是位于拼接图像空间中的单个 PNG 图像（或坐标 TXT 文件）。掩码图像中每个像素的灰度值（材料表中的 `mask_label`）指定拼接图像相应像素（相同 mipmap 级别）的材料类型。在没有特殊处理的情况下，FEABAS 会在 `缩略图对齐 > 下采样` 步骤期间自动为每个切片生成掩码。这些掩码与缩略图处于相同的 mipmap 级别，并假设切片在成像的 ROI 内具有正常属性（平滑变形）。如前所述，用户可以在缩略图对齐过程中修改这些掩码以修正严重的伪影，如分裂的切片。随后在精细对齐步骤中，FEABAS 默认使用这些缩略图掩码。但是，用户可以在 `(work_dir)/align/material_masks` 文件夹中提供更高分辨率的更精确掩码，并在 `alignment_configs.yaml` 文件中指定它们的 mipmap 级别。如果在精细对齐工作流程的网格生成/匹配步骤中有更高质量的掩码可用，FEABAS 将自动使用它们。
此类掩码的生成超出了本包的范围。它可以手动完成，也可以由用户尝试我们来自哈佛大学 Pfister 实验室的合作者开发的专用深度学习工具 [PyTorch Connectomics](https://connectomics.readthedocs.io/en/latest/tutorials/artifact.html)。
