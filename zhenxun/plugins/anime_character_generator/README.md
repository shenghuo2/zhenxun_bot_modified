# 二次元角色生成器

这个插件为用户生成专属的二次元角色形象，并支持使用 NovelAI 生成对应的角色图像。

## 功能说明

### #二次元的我
- **命令**: `#二次元的我`
- **功能**: 生成专属于用户的二次元角色形象
- **特点**: 
  - 使用用户的昵称作为角色名称
  - 提供中文口语化描述
  - 包含英文标签便于进一步使用
  - 智能的属性概率分配
  - 超级用户无视冷却时间

### #生成角色图像
- **命令**: `#生成角色图像 <提示词>`
- **功能**: 根据提示词使用 NovelAI 生成角色图像
- **要求**: 需要先配置 NovelAI 账户信息
- **示例**: `#生成角色图像 1girl, anime style, long hair, school uniform`

### 管理员命令

#### #novelai配置
- **命令**: `#novelai配置 <API_Token>`
- **权限**: 仅超级用户
- **功能**: 配置 NovelAI API Token 并启用图像生成功能

#### #测试novelai
- **命令**: `#测试novelai`
- **权限**: 仅超级用户
- **功能**: 测试 NovelAI 连接是否正常

## 角色属性说明

生成的角色包含以下属性：
- **发色**: 多种颜色选择
- **发型**: 各种二次元经典发型
- **发长**: 从很短到超长的不同长度
- **胸部大小**: 符合二次元设定的不同尺寸
- **眼睛颜色**: 丰富的瞳色选择
- **年龄组**: loli(30%)、teenage(50%)、mature_female(20%)
- **特殊属性**: 服装、配饰、角色设定等

## 使用示例

```
用户: #二次元的我
机器人: ✨ 小明的二次元形象：

二次元的小明，身高标准身高，银发很长的头发的双马尾，大胸部(D)，瞳色蓝色眼睛，属性是恶魔、厚底高跟鞋、铅笔裙，是青春活力的少女

🏷️ 标签：teenage, very_long_hair, silver_eyes, twintails, big_breasts, platinum_blonde_hair, devil, platform_heels, pencil_dress
```

## 安装和配置

### 1. 安装依赖

```bash
pip install novelai_python>=1.0.0 Pillow>=9.0.0 python-dotenv>=0.19.0
```

或者直接安装 requirements.txt：
```bash
pip install -r requirements.txt
```

### 2. 配置 NovelAI API Token（可选）

如果需要使用图像生成功能，可以通过以下方式配置：

#### 方式一：在 `config.yaml` 中添加配置

```yaml
# NovelAI 配置
novelai:
  api_token: "pst-your_api_token_here"  # NovelAI API Token
```

#### 方式二：在 `.env` 文件中设置

```env
NOVELAI_API_TOKEN=pst-your_api_token_here
```

### 3. 测试连接

配置完成后可以测试连接：

```
#测试novelai
```

## 使用流程

1. **生成角色描述**: 使用 `#二次元的我` 生成角色描述
2. **生成角色图像**: 使用 `#生成角色图像 <提示词>` 生成对应图像
3. **管理功能**: 超级用户可以配置和测试 NovelAI 连接

## 冷却机制

- **普通用户**: 个人冷却时间 5 分钟，全局冷却时间 10 秒
- **超级用户**: 无视所有冷却时间
- **图像生成**: 默认冷却时间 30 秒（可在配置中调整）

## 技术特点

- 使用智能概率分配确保角色多样性
- 支持中英文双语输出
- 集成 NovelAI 图像生成功能
- 模块化设计便于扩展
- 完整的错误处理机制
- 支持超级用户权限管理

## 文件结构

```
anime_character_generator/
├── __init__.py          # 主插件文件
├── utils.py            # 角色生成工具函数
├── image_generator.py  # NovelAI 图像生成模块
├── config.py          # 配置管理模块
├── requirements.txt   # 依赖列表
└── README.md         # 说明文档
```

## 📝 说明

本插件使用 `novelai_python` 库通过 NovelAI API 生成动漫角色图像。

## 注意事项

1. **依赖安装**：
   - 选项 1：`pip install novelai-api>=3.0.0 Pillow>=9.0.0`（可能存在兼容性问题）
   - 选项 2：`pip install novelai>=1.3.0 Pillow>=9.0.0`（需要 Python 3.12+）
2. **账户配置**：需要有效的 NovelAI 账户和订阅
3. **网络要求**：图像生成需要稳定的网络连接
4. **存储空间**：生成的图像会保存在本地，请确保有足够的存储空间
5. **使用限制**：请遵守 NovelAI 的使用条款和限制
6. **兼容性**：由于 API 变更，建议查看问题说明文档了解最新状态