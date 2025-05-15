#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
这个脚本用于将 Clash 配置文件转换为本地 SOCKS 代理配置。
主要功能：
1. 读取 Clash 配置文件中的代理节点信息
2. 为每个代理节点创建对应的本地 SOCKS 监听器
3. 生成新的配置文件，包含所有监听器和原始代理信息
"""

import yaml
import argparse
import sys
from typing import Dict, List

def convert_to_socks_proxies(input_file: str, start_port: int = 42000) -> Dict:
    """
    将 Clash 配置文件转换为本地 SOCKS 代理配置
    
    工作流程：
    1. 读取并解析输入的 Clash YAML 配置文件
    2. 保留原始代理节点信息
    3. 为每个代理节点创建对应的本地监听器
    4. 生成包含基础设置和监听器的新配置
    
    :param input_file: 输入的 Clash 配置文件路径
    :param start_port: 本地监听器的起始端口号，默认从 42000 开始
    :return: 包含完整配置信息的字典
    :raises ValueError: 当输入文件格式不正确或缺少必要信息时抛出
    """
    print(f"开始处理文件: {input_file}")  # 调试信息
    
    try:
        # 读取并解析 YAML 文件
        with open(input_file, 'r', encoding='utf-8') as f:
            print("正在读取文件...")  # 调试信息
            yaml_data = yaml.safe_load(f)
            print("文件读取完成")  # 调试信息
    except Exception as e:
        print(f"读取文件时出错: {str(e)}", file=sys.stderr)
        raise
    
    # 验证配置文件格式
    if not yaml_data:
        raise ValueError("YAML 文件为空或格式错误")
    
    if 'proxies' not in yaml_data:
        raise ValueError("无效的 Clash 配置文件，缺少 proxies 部分")
    
    if not isinstance(yaml_data['proxies'], list):
        raise ValueError("proxies 部分格式错误，应该是一个列表")
    
    # 获取代理节点数量
    num_proxies = len(yaml_data['proxies'])
    print(f"找到 {num_proxies} 个代理节点")  # 调试信息
    
    # 创建新的配置字典，包含基础设置
    new_config = {
        # 允许局域网访问
        'allow-lan': True,
        # DNS 设置
        'dns': {
            'enable': True,
            'enhanced-mode': 'fake-ip',  # 使用 fake-ip 模式
            'fake-ip-range': '198.18.0.1/16',  # fake-ip 地址范围
            'default-nameserver': ['114.114.114.114'],  # 默认 DNS 服务器
            'nameserver': ['https://doh.pub/dns-query']  # DoH (DNS over HTTPS) 服务器
        },
        'listeners': [],  # 初始化空的监听器列表
        'proxies': yaml_data['proxies']  # 保留原始代理配置
    }
    
    print("正在创建监听器配置...")  # 调试信息
    
    # 为每个代理创建对应的本地 SOCKS 监听器
    new_config['listeners'] = [
        {
            'name': f'mixed{i}',  # 监听器名称，格式为 mixed0, mixed1, ...
            'type': 'mixed',      # mixed 类型支持 HTTP 和 SOCKS 代理
            'port': start_port + i,  # 监听端口号，从 start_port 递增
            'proxy': proxy['name']   # 关联的代理节点名称
        }
        for i, proxy in enumerate(yaml_data['proxies'])
    ]
    
    print("配置转换完成")  # 调试信息
    return new_config

def main():
    """
    主函数：处理命令行参数并执行转换流程
    """
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='将 Clash 代理节点转换为本地 SOCKS 代理')
    parser.add_argument('input', help='输入的 Clash 配置文件路径')
    parser.add_argument('-o', '--output', default='config.yaml', help='输出的配置文件路径')
    parser.add_argument('-p', '--port', type=int, default=42000, help='起始端口号')
    
    try:
        args = parser.parse_args()
        print(f"参数解析完成: 输入={args.input}, 输出={args.output}, 端口={args.port}")  # 调试信息
    except Exception as e:
        print(f"参数解析错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # 执行转换
        config = convert_to_socks_proxies(args.input, args.port)
        
        # 将新配置写入文件
        print(f"正在写入配置到文件: {args.output}")  # 调试信息
        with open(args.output, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        # 输出转换结果信息
        print(f"转换成功！配置文件已保存到 {args.output}")
        print(f"起始端口: {args.port}, 结束端口: {args.port + len(config['proxies']) - 1}")
        print("\n生成的监听器:")
        for listener in config['listeners']:
            print(f"- {listener['name']}: socks5://127.0.0.1:{listener['port']} (代理: {listener['proxy']})")
    
    except Exception as e:
        print(f"转换失败: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()