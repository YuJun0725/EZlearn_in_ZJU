# 杭州 POI 数据目录

- `raw/amap_pois.json`：带采集元数据的高德原始 POI 快照。
- `review/hangzhou_poi_review.csv`：用于人工整理和补全字段的表格，不代表官方逐条复核。
- `processed/hangzhou_pois_draft.jsonl`：标准化草稿数据，不作为正式规划输入。
- `processed/hangzhou_pois.jsonl`：行程规划器实际使用的最终数据集。
- `processed/validation_report.json`：缺失字段和无效字段的校验报告。

JSON 和 JSONL 文件使用 UTF-8 编码。核验 CSV 使用带 BOM 的 UTF-8 编码，确保它
在 Windows Excel 中打开时可以正确显示中文。

`planning_ready=true` 只表示记录具备规划器要求的字段并通过格式检查，不代表票价、
开放时间或预约规则已经通过景区官方来源核验。
