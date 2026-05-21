# MC Bot运行插件

## 功能描述

这个插件允许超级用户通过SSH将Minecraft命令发送到远程服务器。插件会创建一个临时文件，将MCID和命令写入文件，然后使用paramiko库通过SFTP将文件传输到指定的远程服务器。

## 功能特性

- 🔐 **权限控制**：只有白名单用户才能使用 MC 运行命令
- 🛡️ **命令限制**：仅支持安全的 `spawn` 和 `kill` 命令
- 👥 **白名单管理**：超级用户可以管理白名单用户
- 📝 **详细日志**：记录所有操作和错误信息

## 使用方法

### 基本命令

```
#mcrun <mcid> <command>
```

- `mcid`: Minecraft玩家ID或标识符
- `command`: 要执行的Minecraft命令（支持 spawn、kill 和 status）

### 支持的命令

- `spawn` - 生成/重生相关命令
- `kill` - 击杀相关命令
- `status` - 查看服务器状态

### 示例

```
#mcrun player123 spawn
#mcrun admin kill
#mcrun status
```



## 配置说明

### SSH配置

插件默认配置：
- **主机**: `ciallo.band`
- **用户**: `shenghuo2`
- **目标文件**: `~/tmp.txt`

### 认证方式

插件支持两种SSH认证方式：

1. **密码认证**（默认）
   - 系统会提示输入SSH密码
   - 适合临时使用

2. **密钥认证**（推荐）
   - 使用 `#mcrun_config <密钥路径>` 设置SSH私钥路径
   - 更安全，无需每次输入密码
   - 示例：`#mcrun_config ~/.ssh/id_rsa`

## 工作流程

1. 用户发送 `#mcrun <mcid> <command>` 命令
2. 插件创建临时文件 `tmp.txt`
3. 将 `<mcid> <command>` 写入临时文件
4. 使用paramiko库通过SFTP将文件传输到 `shenghuo2@ciallo.band:~/tmp.txt`
5. 清理本地临时文件
6. 返回执行结果

## 权限要求

- 仅限**超级用户**使用
- 需要安装paramiko库（`pip install paramiko>=2.7.0`）
- 需要对目标服务器的SSH访问权限

## 错误处理

插件包含完善的错误处理机制：
- 参数验证
- SSH连接超时处理（30秒）
- 临时文件自动清理
- 详细的错误信息反馈

## 安全注意事项

1. **权限控制**: 插件仅允许超级用户使用
2. **命令验证**: 建议在远程服务器端进行命令白名单验证
3. **SSH安全**: 推荐使用密钥认证而非密码认证
4. **日志记录**: 所有操作都会记录到日志中

## 系统要求

- Python 3.8+
- paramiko库 (>=2.7.0)
- 对目标服务器的SSH访问权限

## 故障排除

### 常见问题

1. **"paramiko模块未找到"**
   - 确保已安装paramiko库：`pip install paramiko>=2.7.0`
   - 检查Python环境是否正确

2. **"Permission denied"**
   - 检查SSH用户名和密码/密钥
   - 确认对目标服务器的访问权限

3. **"Connection timeout"**
   - 检查网络连接
   - 确认目标服务器地址正确
   - 检查防火墙设置

4. **"Host key verification failed"**
   - 首次连接需要确认主机密钥
   - paramiko会自动处理主机密钥验证

5. **"SFTP传输失败"**
   - 检查目标目录权限
   - 确认SSH连接稳定性

## 更新日志

### v1.0
- 初始版本
- 支持基本的SCP文件传输功能
- 支持密码和密钥认证
- 完善的错误处理和日志记录