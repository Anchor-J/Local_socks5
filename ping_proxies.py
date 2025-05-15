#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
这个脚本用于测试本地SOCKS5代理的连接状态和性能
功能：
1. 读取由convert_to_socks_proxies.py生成的配置文件
2. 测试每个代理的连接状态（失败节点会重试3次）
3. 获取每个代理的实际IP地址和地理位置
4. 测量连接延迟
5. 将结果输出为表格
"""

import yaml
import requests
import time
import socket
import pandas as pd
import concurrent.futures
from tqdm import tqdm
import argparse
import sys
import json

# 设置超时时间
TIMEOUT = 8  # 秒
MAX_RETRIES = 3  # 最大重试次数

def load_config(config_file):
    """
    读取配置文件
    
    :param config_file: 配置文件路径
    :return: 配置字典
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"读取配置文件时出错: {str(e)}", file=sys.stderr)
        sys.exit(1)

def test_single_proxy_attempt(proxy_info):
    """
    单次测试代理连接
    
    :param proxy_info: 代理信息字典
    :return: 包含测试结果的字典和成功标志
    """
    name = proxy_info["name"]
    port = proxy_info["port"]
    proxy_name = proxy_info["proxy"]
    proxy_url = f"socks5://127.0.0.1:{port}"
    
    result = {
        "名称": name,
        "代理名": proxy_name,
        "端口": port,
        "代理地址": proxy_url,
        "状态": "失败",
        "IP地址": "-",
        "国家/地区": "-",
        "城市": "-",
        "运营商": "-",
        "延迟(ms)": "-"
    }
    
    # 设置代理
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    
    success = False
    # 测试连接
    try:
        # 计时开始
        start_time = time.time()
        
        # 通过代理获取IP信息
        response = requests.get('https://api.ipify.org?format=json', 
                               proxies=proxies, 
                               timeout=TIMEOUT)
        
        # 计算延迟
        elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
        
        if response.status_code == 200:
            ip_address = response.json()['ip']
            
            # 获取IP地理位置信息
            geo_response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=TIMEOUT)
            if geo_response.status_code == 200:
                geo_data = geo_response.json()
                country = geo_data.get('country', '-')
                city = geo_data.get('city', '-')
                org = geo_data.get('org', '-')
            else:
                country = "未知"
                city = "未知"
                org = "未知"
            
            # 更新结果
            result.update({
                "状态": "成功",
                "IP地址": ip_address,
                "国家/地区": country,
                "城市": city,
                "运营商": org,
                "延迟(ms)": f"{elapsed:.2f}"
            })
            success = True
    except requests.exceptions.Timeout:
        # 连接超时
        result["状态"] = "超时"
    except requests.exceptions.ProxyError:
        # 代理错误
        result["状态"] = "代理错误"
    except requests.RequestException as e:
        # 连接失败
        result["状态"] = f"失败: {type(e).__name__}"
    except Exception as e:
        # 其他错误
        result["状态"] = f"错误: {type(e).__name__}"
    
    return result, success

def test_proxy(proxy_info):
    """
    测试单个代理，失败时最多重试3次
    
    :param proxy_info: 代理信息字典
    :return: 包含测试结果的字典
    """
    # 第一次尝试
    result, success = test_single_proxy_attempt(proxy_info)
    
    # 如果成功，直接返回结果
    if success:
        return result
    
    # 失败后重试
    retry_count = 1
    while retry_count < MAX_RETRIES:
        retry_count += 1
        # 稍微等待一下再重试
        time.sleep(1)
        
        print(f"正在重试 {proxy_info['name']} (端口 {proxy_info['port']})，第 {retry_count} 次...")
        retry_result, retry_success = test_single_proxy_attempt(proxy_info)
        
        # 如果重试成功，返回重试的结果
        if retry_success:
            retry_result["状态"] += f" (重试 {retry_count} 次)"
            return retry_result
    
    # 所有重试都失败后，返回最后一次的结果
    result["状态"] += f" (已重试 {MAX_RETRIES} 次)"
    return result

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试SOCKS5代理连接状态和性能')
    parser.add_argument('-c', '--config', default='output.yaml', help='配置文件路径')
    parser.add_argument('-o', '--output', default='proxy_results.csv', help='结果输出文件路径')
    parser.add_argument('-t', '--threads', type=int, default=5, help='并发测试线程数')
    parser.add_argument('-n', '--num', type=int, default=0, help='要测试的代理数量，0表示全部')
    args = parser.parse_args()
    
    # 读取配置文件
    print(f"正在读取配置文件: {args.config}")
    config = load_config(args.config)
    
    if 'listeners' not in config:
        print("配置文件中没有找到listeners部分", file=sys.stderr)
        sys.exit(1)
    
    proxies = config['listeners']
    
    # 如果指定了数量，只测试指定数量的代理
    if args.num > 0 and args.num < len(proxies):
        proxies = proxies[:args.num]
        
    print(f"找到 {len(proxies)} 个代理配置")
    
    # 创建结果列表
    results = []
    
    # 使用线程池进行并发测试
    print(f"开始测试，使用 {args.threads} 个并发线程")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        # 提交所有任务并使用tqdm显示进度
        futures = [executor.submit(test_proxy, proxy) for proxy in proxies]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="测试进度"):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"测试过程中出错: {str(e)}", file=sys.stderr)
    
    # 如果没有结果，退出
    if not results:
        print("没有测试结果", file=sys.stderr)
        sys.exit(1)
    
    # 创建DataFrame并按状态和延迟排序
    df = pd.DataFrame(results)
    
    # 将延迟列转换为数值类型进行排序
    df['延迟数值'] = pd.to_numeric(df['延迟(ms)'].str.replace('-', 'NaN'), errors='coerce')
    
    # 添加序号列
    df['序号'] = range(1, len(df) + 1)
    
    # 按照端口列升序排序
    df = df.sort_values('端口', ascending=True)
    
    # 重新调整序号
    df['序号'] = range(1, len(df) + 1)
    
    # 重新调整列顺序，将序号放在最前面
    cols = df.columns.tolist()
    cols.remove('序号')
    df = df[['序号'] + cols]
    
    # 删除临时的延迟数值列
    df = df.drop('延迟数值', axis=1)
    
    # 保存结果到CSV
    df.to_csv(args.output, index=False, encoding='utf-8-sig')
    
    # 统计各状态数量
    status_counts = {}
    for status in df['状态']:
        base_status = status.split(" (")[0]  # 提取基本状态，忽略重试信息
        status_counts[base_status] = status_counts.get(base_status, 0) + 1
    
    success_count = status_counts.get('成功', 0)
    
    # 显示结果统计
    print(f"\n测试完成！总计: {len(proxies)} 个代理")
    print(f"成功: {success_count} ({success_count/len(proxies)*100:.2f}%)")
    
    # 输出状态统计
    for status, count in status_counts.items():
        if status != '成功':
            print(f"{status}: {count} ({count/len(proxies)*100:.2f}%)")
    
    print(f"\n结果已保存到: {args.output}")
    
    # 打印一些示例结果
    if not df.empty:
        # 只显示成功的代理
        success_df = df[df['状态'].str.startswith('成功')]
        if not success_df.empty:
            print("\n成功连接的代理示例:")
            print(success_df.head(5).to_string(index=False))

if __name__ == '__main__':
    main() 