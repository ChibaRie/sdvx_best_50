# SDVX B50 — 图片轻量化 + Volforce 占比显示

日期：2026-08-05

## 背景

当前 `b50.png` 为 1200×3128 RGB PNG，文件约 5.2MB。封面为照片类游戏素材，
按 PNG 无损存储导致体积巨大。同时用户希望了解 B50 中每首歌对总 VOLFORCE 的
贡献占比。

目标：
1. 降低输出图片的像素尺寸与文件体积（轻量化）。
2. 在卡片上显示每首歌对总 VOLFORCE 的贡献百分比。

## 决策

- **图片策略**：画布缩到 800px 宽 + 输出格式改为 JPEG（quality 90, optimize, progressive）。
- **占比显示**：卡片右下角 VF 数值旁追加占比（如 `250.0 ·12.3%`）。

## 一、图片轻量化

### 布局等比缩放（1200 → 800px 宽）

`render_png.py` 布局常量调整（约 0.66×）：

| 常量 | 当前 | 新值 |
|------|------|------|
| `CANVAS_W` | 1200 | 800 |
| `MARGIN_X` | 24 | 15 |
| `MARGIN_Y` | 20 | 14 |
| `HEADER_H` | 80 | 56 |
| `CARD_W` / `COVER_H` | 220 | 146 |
| `CARD_H` | 290 | 192 |
| `CARD_GAP` | 12 | 10 |

校验：`15×2 + 146×5 + 10×4 = 800` ✅

10 行高度：`56 + 14 + 10×(192+10) − 10 + 14 ≈ 2094` → 输出约 **800×2094**。

字号同比例缩小（实现时可微调保证 7px 小字清晰）：
- header_name 26→17, header_meta 16→11, title 14→9, small 11→7, vf 13→9, ex 10→7

### 输出格式 PNG → JPEG

- `canvas.save()` 改为 JPEG：`quality=90, optimize=True, progressive=True`
- 图像为全不透明 RGB，JPEG 无透明通道问题
- 深色 UI + 白字在 q90 下压缩痕迹可忽略
- 目标体积 **~0.4-0.6MB**（降 90%+）

### 文件命名与文档

- 输出名 `b50.png` → `b50.jpg`（`gen_b50.py` 与 README 同步）
- README 规格表更新（尺寸 / 格式 / 体积）
- 重新生成 `assets/preview.png` + `assets/preview_sm.png`

## 二、Volforce 占比

### 数据层（`b50data.py`）

- `build_rows()` 内部计算精确 VF 总和 `vf_sum = sum(r.volforce for r in top)`
  （不经过 `/1000` 取整，避免舍入误差）
- 每行新增字段 `"vf_pct"` = `round(单曲VF / vf_sum × 100, 1)`（保留 1 位小数）
- 边界：`vf_sum == 0` 时所有行 `vf_pct = 0`（避免除零）
- 单一数据源 → PNG 与 HTML 共用，便于测试断言

### PNG 卡片（`render_png.py`）

- 右下角 VF 文本由 `f"{r['volforce']}"` 改为 `f"{r['volforce']} ·{r['vf_pct']}%"`
  （保持青色 VF_COLOR）

### HTML（`render_html.py`）

- VF 列后追加 `VF占比` 列，显示 `12.3%`

## 三、测试更新

| 用例 | 变更 |
|------|------|
| `test_render_png_card_grid_no_overlap` | 宽度断言 1200→800，高度断言 ≥3100→≥2000 |
| 新增 | 输出为 JPEG（`img.format == "JPEG"`）、文件明显变小 |
| 新增 | `vf_pct` 数值正确（各占比求和 ≈100%） |
| 新增 | PNG 卡片文本含 `·12.3%` 格式 |
| 新增 | HTML 含占比列 |

`select_best50`/`build_rows` 现有测试不受影响（`vf_pct` 只是新增键）。

## 范围外

- 不改变 HTML 的封面压缩方式（仍 base64 内嵌 PNG）
- 不引入 WebP / 多分辨率选项（YAGNI）
