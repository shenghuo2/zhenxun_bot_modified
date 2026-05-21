# GPT改图 插件配置说明

## 供应商

`PROVIDERS` 列表, 每项包含:

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | str | 供应商名称 |
| `base_url` | str | API 地址, 自动拼接 `/images/generations` `/images/edits` |
| `api_key` | str | API Key |
| `model` | str | 模型名, `gpt-image-2` |
| `returns_b64` | bool | 是否返回 b64_json (否则为 url) |
| `size_faithful` | bool | 是否遵守请求尺寸; False 则自定义分辨率时自动跳过 |
| `cost_per_call` | float/None | 按次计费单价 (RMB), 与 token 计费二选一 |
| `cost_per_million_input_tokens` | float/None | 输入 token 单价 ($/1M), 与 output 配对使用 |
| `cost_per_million_output_tokens` | float/None | 输出 token 单价 ($/1M) |
| `cost_per_million_tokens` | float/None | 统一 token 单价 (不分输入输出) |

## 重试链

```python
SUPERUSER_RETRY_CHAIN = ["Self", "NowCoding", "ClawNode"]
REGULAR_RETRY_CHAIN = ["Self", "GPTGod", "NowCoding"]
```

- 按顺序尝试, 失败自动切换下一个
- 需要自定义分辨率时自动跳过 `size_faithful=False` 的供应商
- 用户可通过 `--provider=self` 或 `-p=clawnode` 指定供应商 (大小写不敏感)

## 限制配置

```python
COOLDOWN_EXTRA_SECONDS = 60   # 成功后冷却 = 生成耗时 + 此值
COOLDOWN_FAIL_SECONDS = 30    # 失败/取消冷却
DAILY_LIMIT = 5               # 默认每日免费次数
MAX_COUNT_REGULAR = 3         # 单次最大张数
GROUP_DAILY_LIMITS = {        # 按群覆盖每日限额
    "1040437158": 10,
}
```

- 每日免费次数按 **(用户+群/私聊)** 隔离, 按天重置
- 生成中禁止并发请求

## 生成参数

```python
DEFAULT_QUALITY = "medium"  # low/medium/high/max
DEFAULT_COUNT = 1
QUALITY_VALUES = {"low", "medium", "high", "max"}
REQUEST_TIMEOUT = 600       # API 超时 (秒)
```

## 预设比例尺

`PRESET_RATIOS` — 全部满足 API 约束 (≤3:1, 16px 对齐):

`1:1` `1:2` `1:3` `2:1` `3:1` `2:3` `3:2` `3:4` `4:3` `16:9` `9:16`

## 分辨率预设

```python
SIZE_PRESETS = {"1k": ~1M px, "2k": ~4M px}
```

## API 约束

| 约束 | 值 |
|------|-----|
| 对齐 | 16px |
| 比例 | ≤3:1 |
| 像素范围 | 655,360 ~ 8,294,400 |
| 最大边长 | <3,840px |

## 管理员命令

`#gpt改图 添加次数 <qq号>` — superuser 专用, 添加永久次数 (不失效)

## 永久次数

- 优先消耗每日免费额度, 超出部分自动扣永久次数
- 永久次数跨群共享, 不失效

## 快捷指令 (预留)

```python
SHORTCUT_PRESETS: dict[str, dict] = {}
# 格式: {"名称": {"image_urls": [...], "prompt": "...", "size": "1k", "ratio": "1:1"}}
```
