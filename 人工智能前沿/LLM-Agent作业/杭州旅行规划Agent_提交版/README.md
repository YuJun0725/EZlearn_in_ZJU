# 杭州旅行规划 Agent

本项目实现了一个可运行、可评测的杭州旅行规划 Agent。系统当前可以加载69条杭州
POI，结合结构化偏好、天气、路线、开放时间和预算生成逐日行程，并在输出前执行
独立约束校验。自然语言解析可选用任意 OpenAI 兼容接口，其余核心流程均为确定性
Python代码，不依赖第三方包。

课程实验的完整设计、实现、运行方法、测试结果与分析见
[`项目总报告.md`](项目总报告.md)。

## 1. 配置高德 Web 服务 Key

在 PowerShell 中执行：

```powershell
Copy-Item .env.example .env
notepad .env
```

在 `.env` 中填写高德 Web 服务 Key：

```dotenv
AMAP_API_KEY=你的高德Web服务Key
```

`.env` 已经被 Git 忽略。不要将 Key 直接写入 Python 代码，也不要把真实 Key
提交到代码仓库。

## 2. 进行小规模采集测试

先使用一个关键词和一页数据测试 API：

```powershell
python scripts/fetch_amap_pois.py --keywords "博物馆" --pages 1 --limit 10
```

成功后将生成：

- `data/raw/amap_pois.json`：高德返回的原始 POI 数据快照。
- `data/processed/hangzhou_pois_draft.jsonl`：标准化草稿数据，不作为正式规划输入。
- `data/review/hangzhou_poi_review.csv`：用于人工核验和补全的表格。

如果高德返回 `USERKEY_PLAT_NOMATCH`，请检查申请的 Key 是否属于
“Web 服务”，而不是 JavaScript、Android 或其他平台的 Key。

如果出现 `CERTIFICATE_VERIFY_FAILED`，说明 Python 找不到可信的 HTTPS 根证书，
并非高德 Key 错误。采集器会自动寻找环境变量、`certifi`、MSYS2 和 Git for
Windows 自带的 CA 文件。仍然失败时可以显式指定证书：

```powershell
python scripts/fetch_amap_pois.py --keywords "博物馆" --pages 1 --limit 10 `
  --ca-bundle "F:\msys64\usr\ssl\cert.pem"
```

也可以安装 `certifi` 后重新运行：

```powershell
python -m pip install certifi
```

不要通过关闭 SSL 校验解决该问题，否则 API Key 和返回数据可能受到中间人攻击。

## 3. 采集完整候选集

小规模测试成功后运行：

```powershell
python scripts/fetch_amap_pois.py --pages 2 --limit 100 --overwrite-review
```

采集关键词、POI 类别、默认停留时间和室内外属性定义在
`config/amap_keywords.json` 中。默认配置最多发起 24 次搜索请求；如果某个关键词
提前没有下一页数据，程序会停止该关键词的后续请求。

采集器会自动完成：

- 按关键词分页获取杭州 POI。
- 根据高德 POI ID 去重。
- 按类别轮流选取数据，避免某一种景点占满数据集。
- 保存高德原始字段和采集时间。
- 生成标准化 JSONL 草稿和 Excel 兼容的核验 CSV。

再次运行采集器时，程序默认不会覆盖已经存在的核验 CSV，以保护人工修改。只有
明确传入 `--overwrite-review` 才会替换该文件。

## 4. 人工核验 POI

使用 Excel 打开 `data/review/hangzhou_poi_review.csv`，按以下规则检查：

1. 重复、无关或距离杭州主城区过远的 POI，将 `include` 设置为 `false`。
2. 在 `mon` 至 `sun` 七列填写每天的开放时间，例如 `09:00-17:00`。
3. 闭馆日填写 `closed`。
4. 午间闭馆等分段开放时间填写为 `09:00-12:00|13:00-17:00`。
5. 补充门票价格、是否需要预约、步行强度和官方来源。

字段允许值：

- `indoor`、`requires_reservation`：`true` / `false`，也可以填写 `是` / `否`。
- `walk_level`：`low`、`medium`、`high`。
- `ticket_price_yuan`：免费景点填写 `0`。
- `tags`：多个标签使用 `|` 分隔。

`opening_hours_raw` 是高德返回的营业时间，仅作为人工核验参考。高德
`business.cost` 可能表示人均消费，因此程序不会把它自动写入景点门票字段。

开放时间、票价和预约要求容易发生变化。核心 POI 应优先使用景点官网、官方公众号
或预约页面进行核验，并将链接填入 `official_url`。

高德的 `opening_hours_raw` 可以用于预填固定的周开放规律。先试运行查看解析数量：

```powershell
python scripts/prefill_opening_hours.py
```

确认后写入核验 CSV：

```powershell
python scripts/prefill_opening_hours.py --apply
```

脚本不会覆盖已经填写过任意星期的记录，并会将逐条处理结果写入
`data/processed/opening_hours_prefill_report.json`。使用 `--apply` 时，脚本会按需创建
`data/archive/` 并保存修改前快照。

只有明确的固定周规律会被预填。季节时间不同、多馆区共用一条原文、原文为空或存在
冲突的记录会继续留空，必须人工核验。预填结果仍然只是高德参考值，核心POI应通过
官方来源复核。

当前核验表从最初100条候选清理为71条，其中2个没有固定成人票价的场所标记为
`include=false`，因此最终规划数据集包含69条。历史中间备份已经在数据确认后清理，
需要重新采集时可运行采集脚本生成新的原始快照和核验表。

## 5. 构建并校验最终数据集

人工核验过程中，可以生成包含不完整记录的草稿：

```powershell
python scripts/build_poi_dataset.py --allow-incomplete
```

程序会生成：

- `data/processed/hangzhou_pois.jsonl`：构建后的 POI 数据集。
- `data/processed/validation_report.json`：缺失字段和格式错误报告。

不满足规划要求的记录会被标记为：

```json
{
  "planning_ready": false,
  "quality": {
    "status": "incomplete",
    "issues": ["缺失字段说明"]
  }
}
```

完成全部核验后执行严格构建：

```powershell
python scripts/build_poi_dataset.py
```

如果任意被选中的 POI 缺少路线规划、时间窗或预算计算所需字段，严格构建将失败，
具体问题会写入 `data/processed/validation_report.json`。

## 6. 数据目录结构

```text
data/
  raw/
    amap_pois.json
  review/
    hangzhou_poi_review.csv
  processed/
    hangzhou_pois_draft.jsonl
    hangzhou_pois.jsonl
    validation_report.json
```

- `raw`：保留采集时的原始数据，方便追溯和重新处理。
- `review`：保存人工核验表，不应在重新采集时随意覆盖。
- `processed`：保存 Agent 和行程优化器实际读取的标准化数据。

## 7. 运行测试

项目当前只使用 Python 标准库，不需要安装第三方依赖。运行测试：

```powershell
python -m unittest discover -s tests -v
```

测试覆盖 POI 去重、类别均衡抽样、开放时间解析、布尔值解析和高德字段标准化。

## 8. 加载和查询 POI

项目采用 `src` 目录布局。当项目没有安装为 Python 包时，在当前 PowerShell 会话中设置：

```powershell
$env:PYTHONPATH = "src"
```

加载当前69条 POI，并查看统计信息：

```powershell
python -c "from travel_agent.data import POIRepository; r=POIRepository.from_jsonl(); print(r.statistics())"
```

按中文关键词搜索：

```python
from travel_agent.data import POIRepository
from travel_agent.models import POIQuery

repository = POIRepository.from_jsonl()
results = repository.search_with_scores(
    POIQuery(text="博物馆", districts=("上城区",), limit=5)
)

for result in results:
    print(result.poi.name, result.score, result.matched_fields)
```

按结构化字段筛选：

```python
museums = repository.search(
    POIQuery(
        categories=("museum",),
        indoor=True,
        include_unknown=True,
        planning_ready_only=True,
        limit=20,
    )
)
```

当前 69 条数据均已通过程序要求的字段和格式检查，因此可以使用
`planning_ready_only=True`。需要注意，`planning_ready` 只表示记录可被规划器加载，
不代表票价、开放时间和预约规则已经通过景区官方来源复核。

## 9. 根据结构化偏好选择候选 POI

`POISearchTool` 不调用大模型。它接收已经结构化的旅行偏好，将中文偏好映射为
POI类别，处理必去和避开条件，并返回带分数、推荐理由和数据告警的候选结果。

```python
from travel_agent.data import POIRepository
from travel_agent.models import WalkLevel
from travel_agent.tools import POISearchInput, POISearchTool

repository = POIRepository.from_jsonl()
tool = POISearchTool(repository)

response = tool.search(
    POISearchInput(
        preferences=("历史", "自然"),
        districts=("上城区", "西湖区"),
        must_visit=("南宋德寿宫遗址博物馆",),
        avoid=("动物园",),
        max_walk_level=WalkLevel.LOW,
        indoor_preferred=False,
        planning_ready_only=False,
        limit=12,
    )
)

for candidate in response.candidates:
    print(candidate.poi.name)
    print(candidate.score)
    print(candidate.selection_reasons)
    print(candidate.data_warnings)

print(response.unresolved_must_visit)
print(response.warnings)
```

当前预设支持历史、人文、文化、博物馆、艺术、展览、自然、户外、公园、湿地、
亲子、动物、古镇、城市、街区和购物等偏好。无法映射的偏好不会丢失，工具会尝试
使用POI名称和标签进行文本匹配，并在响应中返回告警。

## 10. 查询高德路线

路线工具继续使用 `.env` 中现有的 `AMAP_API_KEY`，不需要申请第二个 Key。该 Key
必须属于高德 Web 服务，并具有路线规划接口的可用配额。

```python
from travel_agent.data import POIRepository
from travel_agent.tools import AmapRouteTool, RouteMode

repository = POIRepository.from_jsonl()
origin = repository.find_by_name("南宋德寿宫遗址博物馆", exact=True)[0]
destination = repository.find_by_name("杭州博物馆", exact=True)[0]

route_tool = AmapRouteTool.from_env()
route = route_tool.get_route(
    origin,
    destination,
    mode=RouteMode.WALKING,
)

print(route.distance_m)
print(route.distance_km)
print(route.duration_s)
print(route.duration_minutes)
print(route.from_cache)
```

支持的交通方式：

- `RouteMode.WALKING`：调用高德步行路线接口。
- `RouteMode.DRIVING`：调用高德驾车路线接口。
- `RouteMode.TAXI`：复用驾车路线，只表示出租车行程，不估算车费。

默认缓存文件为 `data/cache/amap_routes.json`，有效期24小时。同一起点、终点和
交通方式在缓存有效期内不会重复消耗高德API额度。传入 `use_cache=False` 可以强制
刷新单条路线；将 `cache_ttl_seconds=None` 传给构造函数可以让缓存永久有效，适合
固定数据快照的对比实验。

POI坐标来自高德，属于 GCJ-02 坐标系，可以直接传给路线接口。不要把未经转换的
WGS-84坐标与高德POI坐标混用。

## 11. 查询高德天气

天气工具同样复用 `.env` 中的 `AMAP_API_KEY`。杭州默认使用行政区编码 `330100`。

```python
from travel_agent.tools import AmapWeatherTool

weather_tool = AmapWeatherTool.from_env()

current = weather_tool.get_current()
print(current.condition)
print(current.temperature_c)
print(current.indoor_recommended)
print(current.assessment.advisories)

forecast = weather_tool.get_forecast()
for day in forecast:
    print(day.date, day.day_condition, day.indoor_recommended)

travel_day = weather_tool.get_for_date("2026-07-26")
```

天气建议可以直接传给候选POI搜索：

```python
from travel_agent.tools import POISearchInput

criteria = POISearchInput(
    preferences=("历史", "自然"),
    indoor_preferred=travel_day.indoor_recommended,
    limit=12,
)
```

工具会将天气转换成确定性旅行建议：

- 雨、雪、强对流天气：`indoor_recommended=True`。
- 最高温度达到35摄氏度：减少午间户外活动。
- 最低温度不高于0摄氏度：减少长时间户外停留。
- 正常晴天或多云：`outdoor_suitable=True`。

实时天气默认缓存30分钟，未来预报默认缓存3小时，缓存文件为
`data/cache/amap_weather.json`。缓存中不保存API Key。高德只提供有限天数的预报；
查询超出预报窗口的日期时，工具会明确返回当前可用日期，不会编造远期天气。

## 12. 完整项目架构

```text
src/travel_agent/
  config.py                 环境变量和规划参数
  models.py                 POI、旅行需求、行程、预算、校验结果等领域模型
  data/poi_repository.py    稳定加载、索引、筛选和查询POI
  services/amap_client.py   高德HTTP、SSL、重试等公共能力
  tools/
    poi_search.py           结构化偏好到候选POI
    amap_route.py           高德步行/驾车路线与缓存
    weather.py              高德天气、缓存和确定性天气建议
    budget.py               门票、交通、餐饮和总预算估算
  planner/
    optimizer.py            基于得分、距离和时间窗的贪心优化
    itinerary.py            生成逐日到达/离开时间和费用
    validator.py            独立检查时间、预算、重复和必去约束
  llm/client.py             可选OpenAI兼容自然语言解析器
  agent/
    prompts.py              旅行需求抽取提示词
    graph.py                显式Agent状态机和一次重规划
  presentation/cli.py       人类可读的命令行行程展示
tests/                      单元测试和当前POI快照端到端测试
eval/scenarios.json         固定离线评测场景
eval/run_evaluation.py      评测指标计算
app.py                      命令行入口
```

这里的 `graph.py` 不依赖 LangGraph，而是使用显式状态机完成以下步骤：

```text
需求校验 -> 天气 -> POI检索 -> 行程规划 -> 约束校验
                                      |          |
                                      +--重规划--+
```

每个阶段都会生成 `ToolTrace`。最终JSON中的 `traces` 可以用于课程报告中的工具调用
轨迹、失败降级和可解释性展示。LLM只将自然语言转换为 `TravelRequest`，不会直接生成
POI、价格或路线，从而避免把模型幻觉混入规划结果。

## 13. 运行完整 Agent

不传参数或使用 `--demo` 会运行内置的两日杭州离线示例，不调用任何网络API：

```powershell
python app.py
python app.py --demo
```

使用结构化JSON字符串：

```powershell
python app.py --request-json '{"city":"杭州市","days":2,"preferences":["历史","自然"],"budget_yuan":1000}'
```

需求较长时建议建立UTF-8 JSON文件，再运行：

```powershell
python app.py --request-file request.json
```

默认输出是适合直接阅读的命令行行程，包含：

- 结构化后的旅行需求摘要。
- 每天的POI顺序、到达/离开时间和站间交通。
- 门票、交通、餐饮、总额和预算余额。
- 合并后的数据质量提醒和硬约束校验结果。
- 根据已校验行程自动生成的自然语言行程说明；使用 `--json` 时字段名为 `natural_language_output`。

将可读行程同时保存到文本文件：

```powershell
python app.py --demo --output outputs/demo_plan.txt
```

课程实验或程序调用需要完整结构化数据时，使用 `--json`：

```powershell
python app.py --demo --json
python app.py --demo --json --output outputs/demo_plan.json
```

需要在演示中查看 Agent 工具调用过程时，使用：

```powershell
python app.py --demo --show-trace
```

开启高德实时天气和逐段路线：

```powershell
python app.py --request-file request.json --live-weather --live-routes
```

外部天气或路线请求失败时，Agent会在 `traces` 中记录 `degraded`，并使用离线距离、
时间估算继续运行。未启用实时能力时不会消耗高德配额。

## 14. 配置自然语言输入

自然语言输入需要在 `.env` 中增加三个变量：

```dotenv
LLM_API_KEY=你的大模型APIKey
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

等号右侧通常不需要引号。程序也支持带单引号或双引号的值，并会在加载时自动去掉
最外层引号。使用阿里云百炼Qwen等服务时，将 `LLM_BASE_URL` 和 `LLM_MODEL` 换成
该服务提供的OpenAI兼容地址和模型名即可。

配置后运行：

```powershell
python app.py --text "两个人去杭州玩两天，喜欢历史和美术，预算1200元，德寿宫必去"
```

大模型必须抽取出旅行天数。若自然语言没有说明天数，Agent会返回需要补充的信息，
不会自行猜测。LLM Key仅放在请求头中，不会写入结果或缓存。

## 15. 离线评测

运行固定场景：

```powershell
python eval/run_evaluation.py
```

保存评测报告：

```powershell
python eval/run_evaluation.py --output eval/report.json
```

当前评测报告包含：

- 场景完成率和硬约束满足率。
- 必去POI完成率。
- 预算是否满足和预计总费用。
- 每个场景的POI数量、警告数和错误数。

评测默认完全离线，保证重复运行结果稳定。可以编辑 `eval/scenarios.json` 增加不同
人群、预算、偏好和时间窗场景。

## 16. 当前数据限制

当前 69 条 POI 已全部标记为 `planning_ready=true`，可以支撑完整架构联调；该字段
只表示必填字段和格式通过检查。当前 69 条记录的 `official_url` 均为空，官方来源
覆盖率为 0/69。程序和报告需明确以下数据适用范围：

- 未核验开放时间使用 `09:00-17:00` 默认时间窗。
- 52 条票价记录为 0，可能表示免费，也可能仍需核验；程序会按当前数值计算。
- 17 条记录为非零票价，但仍需用官方来源确认。
- 出租车费用按简化计价规则估算。
- 离线路线使用球面距离和道路系数估算。

因此，程序输出的“预算合规”只表示按当前开发数据和估算规则未超过预算，不代表
现实消费一定准确。真实出行时应以景区官方发布的价格、开放时间和预约规则为准。
