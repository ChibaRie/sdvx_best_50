# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与
[Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [1.2.1] - 2026-08-05

### 修正

- 修正 GRADE 名称映射：ID=6 错误显示为 "AAA"，现正确显示为 **"AA"**
- 代码中补入完整 VF 公式与系数表注释（CLEAR + GRADE）

## [1.2.0] - 2026-08-05

### 变更

- 卡片布局改为 **5:2 横向长方形**：正方形封面居左（占卡片宽 2/5、填满高度），
  标题 / GRADE / 难度标签 / SCORE / EX SCORE / VF·占比 全部在右侧呈现
- 输出尺寸 1200 × ~1135 px（原 1200 × ~3128），体积进一步降至 ~0.4-1MB

## [0.2.0] - 2026-08-05

### 新增

- **每曲 VOLFORCE 贡献占比**：卡片右下角显示该曲对总 VOLFORCE 的贡献百分比，
  精确到小数点后 4 位，如 `250.0 ·12.3456%`
- HTML 表格新增 `VF占比` 列，展示每曲占比（4 位小数）

### 变更

- 输出格式 PNG → **JPEG**（quality 85，optimize + progressive），
  1200px 分辨率下体积约 0.6-1.2MB，较原 5.2MB 缩减约 75%
- 输出文件名 `b50.png` → `b50.jpg`
- 保持 1200px 高分辨率卡片网格（封面 220×220），保证清晰度

## [0.1.0] - 2026-08-05

### 新增

- 从 asphyxia 氧无存档提取玩家成绩，按 `(mid, type)` 去重并按 VOLFORCE 降序取前 50
- 5 列 × 10 行卡片网格渲染（1200px），含封面 / 曲名 / 难度标签 / 分数 / EX SCORE / GRADE / VF
- 自包含 HTML 输出（封面 base64 内嵌，可浏览器直接打开、打印）
- 微软雅黑字体渲染中日韩文字
- PyInstaller 打包为约 27MB 单文件 exe
