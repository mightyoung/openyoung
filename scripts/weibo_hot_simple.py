#!/usr/bin/env python3
"""
微博热搜简单爬虫
尝试不同的方法来获取微博热搜
"""

import json
import os
from datetime import datetime

import requests


def test_weibo_api():
    """测试不同的微博API"""

    # 尝试不同的User-Agent
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
        {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        },
    ]

    # 尝试不同的API端点
    api_endpoints = [
        "https://weibo.com/ajax/side/hotSearch",
        "https://s.weibo.com/ajax/topsearch/hotword",
        "https://weibo.com/ajax/statuses/hot_band",
        "https://weibo.com/ajax/hot/search",
    ]

    for headers in headers_list:
        for endpoint in api_endpoints:
            try:
                print(f"尝试访问: {endpoint}")
                print(f"使用User-Agent: {headers['User-Agent'][:50]}...")

                response = requests.get(endpoint, headers=headers, timeout=10)
                print(f"状态码: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"成功获取数据，数据结构: {type(data)}")
                        print(
                            f"数据键: {list(data.keys()) if isinstance(data, dict) else '不是字典'}"
                        )

                        # 尝试解析热搜数据
                        if isinstance(data, dict):
                            # 检查常见的数据结构
                            if "data" in data:
                                print("找到 'data' 键")
                                if isinstance(data["data"], dict) and "realtime" in data["data"]:
                                    print("找到热搜数据: data.realtime")
                                    return data
                                elif isinstance(data["data"], list):
                                    print(f"data是列表，长度: {len(data['data'])}")
                                    return data
                            elif "hotgov" in data:
                                print("找到 'hotgov' 键")
                                return data

                        # 保存原始数据用于分析
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"weibo_raw_{timestamp}.json"
                        os.makedirs("output/weibo", exist_ok=True)

                        with open(f"output/weibo/{filename}", "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        print(f"原始数据已保存到: output/weibo/{filename}")
                        return data

                    except json.JSONDecodeError:
                        print("响应不是JSON格式")
                        # 保存HTML响应用于分析
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"weibo_html_{timestamp}.html"
                        os.makedirs("output/weibo", exist_ok=True)

                        with open(f"output/weibo/{filename}", "w", encoding="utf-8") as f:
                            f.write(response.text[:5000])  # 只保存前5000字符

                        print(f"HTML响应已保存到: output/weibo/{filename}")

                elif response.status_code == 403:
                    print("访问被拒绝 (403)")
                elif response.status_code == 404:
                    print("页面不存在 (404)")
                else:
                    print(f"其他错误: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"请求异常: {e}")

            print("-" * 50)

    return None


def parse_weibo_data(data):
    """尝试解析微博数据"""
    if not data:
        return []

    hot_searches = []

    # 尝试不同的数据结构
    if isinstance(data, dict):
        # 结构1: data.realtime
        if "data" in data and isinstance(data["data"], dict):
            realtime_data = data["data"].get("realtime", [])
            if realtime_data and isinstance(realtime_data, list):
                print(f"从data.realtime找到{len(realtime_data)}条数据")
                for i, item in enumerate(realtime_data[:20]):
                    hot_item = {
                        "rank": i + 1,
                        "title": item.get("word", item.get("title", item.get("name", ""))).strip(),
                        "hot_value": item.get("num", item.get("hot", 0)),
                        "label": item.get("label_name", item.get("label", "")),
                        "category": item.get("category", ""),
                        "url": f"https://s.weibo.com/weibo?q={item.get('word', item.get('title', ''))}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    hot_searches.append(hot_item)
                return hot_searches

        # 结构2: 直接是列表
        elif "data" in data and isinstance(data["data"], list):
            print(f"从data列表找到{len(data['data'])}条数据")
            for i, item in enumerate(data["data"][:20]):
                if isinstance(item, dict):
                    hot_item = {
                        "rank": i + 1,
                        "title": item.get("word", item.get("title", item.get("name", ""))).strip(),
                        "hot_value": item.get("num", item.get("hot", 0)),
                        "label": item.get("label_name", item.get("label", "")),
                        "category": item.get("category", ""),
                        "url": f"https://s.weibo.com/weibo?q={item.get('word', item.get('title', ''))}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    hot_searches.append(hot_item)
            return hot_searches

        # 结构3: hotgov
        elif "hotgov" in data and isinstance(data["hotgov"], dict):
            hotgov = data["hotgov"]
            hot_item = {
                "rank": 1,
                "title": hotgov.get("word", hotgov.get("title", "")).strip(),
                "hot_value": hotgov.get("num", 0),
                "label": "置顶",
                "category": "政府",
                "url": f"https://s.weibo.com/weibo?q={hotgov.get('word', '')}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            hot_searches.append(hot_item)
            return hot_searches

    print("无法识别的数据结构")
    return []


def save_results(hot_searches):
    """保存结果"""
    if not hot_searches:
        print("没有数据可保存")
        return

    os.makedirs("output/weibo", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存为JSON
    json_file = f"output/weibo/weibo_hot_{timestamp}.json"
    output_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(hot_searches),
        "hot_searches": hot_searches,
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"JSON文件已保存: {json_file}")

    # 保存为Markdown
    md_file = f"output/weibo/weibo_hot_{timestamp}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# 微博热搜榜\n\n")
        f.write(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**总条数**: {len(hot_searches)}\n\n")
        f.write("| 排名 | 热搜词 | 热度值 | 标签 |\n")
        f.write("|------|--------|--------|------|\n")

        for item in hot_searches:
            rank = item["rank"]
            title = item["title"]
            hot_value = f"{item['hot_value']:,}" if item["hot_value"] else "0"
            label = item["label"] if item["label"] else "-"

            f.write(f"| {rank} | [{title}]({item['url']}) | {hot_value} | {label} |\n")

    print(f"Markdown文件已保存: {md_file}")

    # 显示结果
    print(f"\n成功获取 {len(hot_searches)} 条微博热搜数据:")
    print("-" * 60)
    for item in hot_searches[:10]:  # 只显示前10条
        print(f"{item['rank']:2d}. {item['title']} ({item['hot_value']:,})")


def main():
    """主函数"""
    print("开始测试微博热搜API...")
    print("=" * 60)

    data = test_weibo_api()

    if data:
        print("\n开始解析数据...")
        hot_searches = parse_weibo_data(data)
        save_results(hot_searches)
    else:
        print("\n所有API测试都失败了")

        # 尝试使用备用方案：模拟搜索页面
        print("\n尝试备用方案：使用搜索页面...")
        try:
            # 尝试获取热搜页面
            url = "https://s.weibo.com/top/summary"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            print(f"热搜页面状态码: {response.status_code}")

            if response.status_code == 200:
                # 保存页面用于分析
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"output/weibo/weibo_page_{timestamp}.html"
                os.makedirs("output/weibo", exist_ok=True)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response.text)

                print(f"热搜页面已保存: {filename}")

                # 简单解析HTML（这里只是示例，实际需要更复杂的解析）
                import re

                # 尝试查找热搜词
                pattern = r'<a[^>]*href="/weibo\?q=[^"]*"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, response.text[:10000])  # 只搜索前10000字符

                if matches:
                    hot_searches = []
                    for i, title in enumerate(matches[:20]):
                        hot_item = {
                            "rank": i + 1,
                            "title": title.strip(),
                            "hot_value": 0,  # 无法从简单解析获取热度值
                            "label": "",
                            "category": "",
                            "url": f"https://s.weibo.com/weibo?q={title}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        hot_searches.append(hot_item)

                    save_results(hot_searches)
                else:
                    print("无法从页面中提取热搜词")
            else:
                print("无法访问热搜页面")

        except Exception as e:
            print(f"备用方案失败: {e}")


if __name__ == "__main__":
    main()
