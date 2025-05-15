# test
# SOCKS5代理测试工具

这个工具用于测试本地SOCKS5代理的连接状态和性能。它可以检测每个代理的可用性、IP地址、地理位置和连接延迟。

## 功能

- 读取由 `convert_to_socks_proxies.py` 生成的 YAML 配置文件
- 测试每个代理的连接状态
- 获取每个代理的实际IP地址和地理位置信息（国家/地区、城市、运营商）
- 测量连接延迟
- 将结果输出为CSV表格

## 安装

1. 确保已安装Python 3.7或更高版本
2. 安装依赖包：

```bash
pip install -r requirements.txt
```

## 使用方法

基本用法：

```bash
python test_proxies.py
```

这将使用默认配置（读取`output.yaml`文件）测试所有代理，并将结果保存到`proxy_results.csv`。

高级用法：

```bash
python test_proxies.py -c 配置文件 -o 输出文件 -t 线程数 -n 代理数量
```

参数说明：
- `-c`, `--config`: 指定配置文件路径（默认：`output.yaml`）
- `-o`, `--output`: 指定结果输出文件路径（默认：`proxy_results.csv`）
- `-t`, `--threads`: 指定并发测试线程数（默认：5）
- `-n`, `--num`: 指定要测试的代理数量，0表示全部（默认：0）

示例：

```bash
# 使用8个线程测试前10个代理
python test_proxies.py -t 8 -n 10

# 指定配置文件和输出文件
python test_proxies.py -c config.yaml -o results.csv
```

## 输出结果

脚本会生成一个CSV文件，其中包含以下字段：
- 名称：代理在配置文件中的名称
- 代理名：代理的显示名称
- 端口：本地监听端口
- 代理地址：完整的SOCKS5代理地址
- 状态：连接状态（成功/失败/超时等）
- IP地址：远程服务器的IP地址
- 国家/地区：远程服务器的所在国家或地区
- 城市：远程服务器的所在城市
- 运营商：远程服务器的网络运营商
- 延迟(ms)：连接延迟（毫秒）

## 注意事项

- 测试过程中需要保持代理服务正常运行
- 需要互联网连接以获取IP地理位置信息
- 对于大量代理，可以增加线程数来加快测试速度，但同时也会增加网络负载 