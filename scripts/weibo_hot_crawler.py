#!/usr/bin/env python3
"""
微博热搜爬虫脚本
获取微博热搜榜单前20名并保存到output/weibo目录
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List

import requests


class WeiboHotCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.base_url = "https://weibo.com/ajax/side/hotSearch"
        self.output_dir = "output/weibo"
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_hot_search(self) -> Dict[str, Any]:
        """获取微博热搜数据"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {}
    
    def parse_hot_search_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析热搜数据"""
        hot_searches = []
        
        if not data:
            return hot_searches
        
        # 获取热搜榜数据
        hot_list = data.get('data', {}).get('realtime', [])
        
        for i, item in enumerate(hot_list[:20]):  # 只取前20名
            hot_item = {
                'rank': i + 1,
                'title': item.get('word', '').strip(),
                'hot_value': item.get('num', 0),
                'label': item.get('label_name', ''),
                'category': item.get('category', ''),
                'url': f"https://s.weibo.com/weibo?q={item.get('word', '')}",
                'note': item.get('note', ''),
                'icon': item.get('icon', ''),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            hot_searches.append(hot_item)
        
        return hot_searches
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None):
        """保存数据到JSON文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"weibo_hot_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        output_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(data),
            'hot_searches': data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {filepath}")
        return filepath
    
    def save_to_markdown(self, data: List[Dict[str, Any]], filename: str = None):
        """保存数据到Markdown文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"weibo_hot_{timestamp}.md"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 微博热搜榜\n\n")
            f.write(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**总条数**: {len(data)}\n\n")
            f.write("| 排名 | 热搜词 | 热度值 | 标签 | 分类 |\n")
            f.write("|------|--------|--------|------|------|\n")
            
            for item in data:
                rank = item['rank']
                title = item['title']
                hot_value = f"{item['hot_value']:,}" if item['hot_value'] else "0"
                label = item['label'] if item['label'] else "-"
                category = item['category'] if item['category'] else "-"
                
                f.write(f"| {rank} | [{title}]({item['url']}) | {hot_value} | {label} | {category} |\n")
        
        print(f"Markdown文件已保存到: {filepath}")
        return filepath
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None):
        """保存数据到CSV文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"weibo_hot_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        import csv
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['rank', 'title', 'hot_value', 'label', 'category', 'url', 'note', 'timestamp'])
            writer.writeheader()
            
            for item in data:
                writer.writerow(item)
        
        print(f"CSV文件已保存到: {filepath}")
        return filepath
    
    def run(self):
        """运行爬虫"""
        print("开始获取微博热搜数据...")
        
        # 获取数据
        raw_data = self.fetch_hot_search()
        
        if not raw_data:
            print("获取数据失败")
            return
        
        # 解析数据
        hot_searches = self.parse_hot_search_data(raw_data)
        
        if not hot_searches:
            print("解析数据失败或没有热搜数据")
            return
        
        print(f"成功获取 {len(hot_searches)} 条热搜数据")
        
        # 显示前10条
        print("\n微博热搜榜前10名:")
        print("-" * 80)
        for item in hot_searches[:10]:
            print(f"{item['rank']:2d}. {item['title']} ({item['hot_value']:,})")
        
        # 保存数据
        json_file = self.save_to_json(hot_searches)
        md_file = self.save_to_markdown(hot_searches)
        csv_file = self.save_to_csv(hot_searches)
        
        print("\n数据保存完成:")
        print(f"  JSON文件: {json_file}")
        print(f"  Markdown文件: {md_file}")
        print(f"  CSV文件: {csv_file}")
        
        return hot_searches

def main():
    """主函数"""
    crawler = WeiboHotCrawler()
    crawler.run()

if __name__ == "__main__":
    main()
