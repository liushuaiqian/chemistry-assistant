# Ngrok 设置指南

## 为什么需要下载？

当你第一次运行使用 `pyngrok` 的代码时，你可能会看到下载提示。这是完全正常的行为，原因如下：

### 1. pyngrok 是什么？
- `pyngrok` 是一个 Python 包装器库
- 它提供了 Python 接口来控制 ngrok
- 但它本身不包含 ngrok 的可执行文件

### 2. 为什么需要下载 ngrok 二进制文件？
- ngrok 是一个独立的可执行程序
- `pyngrok` 需要调用这个程序来创建隧道
- 首次使用时，`pyngrok` 会自动下载适合你操作系统的 ngrok 二进制文件

### 3. 下载过程
- 下载只会发生一次
- 文件会保存在本地缓存中
- 后续使用不需要重新下载

### 4. 下载位置
通常 ngrok 二进制文件会下载到：
- Windows: `%USERPROFILE%\.ngrok2\`
- macOS/Linux: `~/.ngrok2/`

## 如何处理？

### 选项1：让它自动下载（推荐）
```python
# 第一次运行时会自动下载
from pyngrok import ngrok
ngrok.set_auth_token("your_token")
public_url = ngrok.connect(8000)
```

### 选项2：手动预下载
```python
from pyngrok import ngrok
from pyngrok.installer import install_ngrok

# 手动安装 ngrok
install_ngrok()
print("Ngrok 已安装完成")
```

### 选项3：使用系统安装的 ngrok
如果你已经在系统中安装了 ngrok，可以配置 pyngrok 使用它：
```python
from pyngrok import conf, ngrok

# 设置 ngrok 可执行文件路径
conf.get_default().ngrok_path = "/path/to/your/ngrok"
```

## 网络要求

- 需要稳定的网络连接
- 可能需要科学上网（取决于网络环境）
- 下载大小约 10-20MB

## 故障排除

### 下载失败
1. 检查网络连接
2. 尝试使用代理
3. 手动下载 ngrok 并配置路径

### 权限问题
1. 确保有写入权限到用户目录
2. 在 Windows 上可能需要管理员权限

## 总结

下载 ngrok 是正常且必要的步骤，这样才能使用 ngrok 的隧道功能。一旦下载完成，后续使用就会很快了。