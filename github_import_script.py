#!/usr/bin/env python3
"""
GitHub Agent 导入脚本
从 GitHub 仓库导入 Agent 配置到本地 OpenYoung 项目
"""

import os
import sys
import subprocess
import shutil
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

class GitHubAgentImporter:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.packages_dir = self.project_root / "packages"
        self.subagents_dir = self.project_root / "subagents"
        self.temp_dir = Path(tempfile.gettempdir()) / "openyoung_imports"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def parse_github_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """解析 GitHub URL，返回 owner 和 repo"""
        url = url.strip().rstrip("/")
        
        # 处理多种格式
        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
        else:
            parts = url.split("/")
            
        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None
    
    def git_clone(self, owner: str, repo: str) -> Optional[Path]:
        """克隆 GitHub 仓库到临时目录"""
        repo_url = f"https://github.com/{owner}/{repo}.git"
        local_path = self.temp_dir / f"{owner}_{repo}"
        
        # 如果目录已存在，先删除
        if local_path.exists():
            shutil.rmtree(local_path)
        
        try:
            print(f"正在克隆 {repo_url}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(local_path)],
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                print(f"成功克隆到 {local_path}")
                return local_path
            else:
                print(f"克隆失败: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("克隆超时")
            return None
        except Exception as e:
            print(f"克隆出错: {e}")
            return None
    
    def analyze_project_structure(self, local_path: Path) -> Dict:
        """分析项目结构，识别关键文件"""
        structure = {
            "languages": [],
            "has_claude_md": False,
            "has_agents_md": False,
            "has_skills": False,
            "has_mcps": False,
            "has_hooks": False,
            "has_evaluation": False,
            "skills": [],
            "mcps": [],
            "hooks": [],
            "evaluations": [],
            "main_prompt": "",
            "subagent_prompts": [],
            "files": []
        }
        
        # 扫描所有文件
        for item in local_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(local_path)
                structure["files"].append(str(relative_path))
                
                # 检测关键文件
                name = item.name.lower()
                if name == "claude.md":
                    structure["has_claude_md"] = True
                    try:
                        content = item.read_text(encoding='utf-8', errors='ignore')
                        structure["main_prompt"] = content[:5000]
                    except:
                        pass
                        
                elif name == "agents.md":
                    structure["has_agents_md"] = True
                    try:
                        content = item.read_text(encoding='utf-8', errors='ignore')
                        structure["subagent_prompts"] = self.parse_agents_md(content)
                    except:
                        pass
                        
                elif "skill" in name and (name.endswith(".yaml") or name.endswith(".json")):
                    structure["has_skills"] = True
                    structure["skills"].append(str(relative_path))
                    
                elif name == "mcp.json" or name == ".mcp.json":
                    structure["has_mcps"] = True
                    structure["mcps"].append(str(relative_path))
                    
                elif name == "hooks.json" or ".cursor/hooks.json" in str(item):
                    structure["has_hooks"] = True
                    structure["hooks"].append(str(relative_path))
                    
                elif "eval" in name and (name.endswith(".yaml") or name.endswith(".json")):
                    structure["has_evaluation"] = True
                    structure["evaluations"].append(str(relative_path))
        
        return structure
    
    def parse_agents_md(self, content: str) -> List[Dict]:
        """解析 AGENTS.md 文件，提取子代理信息"""
        subagents = []
        
        # 简单解析：查找以 ## 开头的部分作为子代理
        lines = content.split('\n')
        current_agent = None
        
        for line in lines:
            if line.startswith('## '):
                if current_agent:
                    subagents.append(current_agent)
                agent_name = line[3:].strip()
                current_agent = {
                    "name": agent_name,
                    "description": "",
                    "content": line + "\n"
                }
            elif current_agent:
                current_agent["content"] += line + "\n"
                
        if current_agent:
            subagents.append(current_agent)
            
        return subagents
    
    def create_agent_config(self, owner: str, repo: str, agent_name: str, 
                           structure: Dict, local_path: Path) -> bool:
        """创建 Agent 配置"""
        # 创建 agent 目录
        agent_dir = self.packages_dir / agent_name
        original_dir = agent_dir / "original"
        
        # 如果目录已存在，先备份
        if agent_dir.exists():
            backup_dir = agent_dir.parent / f"{agent_name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.move(agent_dir, backup_dir)
            print(f"已备份现有配置到 {backup_dir}")
        
        # 创建目录结构
        agent_dir.mkdir(parents=True, exist_ok=True)
        original_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制原始仓库内容
        print(f"复制仓库内容到 {original_dir}...")
        for item in local_path.iterdir():
            if item.name != ".git":
                dest = original_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
        
        # 创建 agent.yaml 配置
        agent_config = {
            "name": agent_name,
            "version": "1.0.0",
            "description": f"Imported from {owner}/{repo}",
            "source_url": f"https://github.com/{owner}/{repo}",
            "model": {"name": "deepseek-chat", "temperature": 0.7},
            "tools": ["read", "write", "edit", "bash", "glob", "grep"],
            "skills": [],
            "mcps": [],
            "sub_agents": [],
            "system_prompt": structure.get("main_prompt", "")[:4000],
        }
        
        # 添加检测到的技能
        if structure.get("skills"):
            agent_config["skills"] = [{"name": "github-import", "version": "1.0.0"}]
        
        # 保存 agent.yaml
        agent_yaml_path = agent_dir / "agent.yaml"
        with open(agent_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(agent_config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"Agent 配置已保存到 {agent_yaml_path}")
        
        # 创建子代理配置
        self.create_subagent_configs(structure, agent_name)
        
        return True
    
    def create_subagent_configs(self, structure: Dict, parent_agent: str):
        """创建子代理配置"""
        subagents = structure.get("subagent_prompts", [])
        
        for subagent in subagents:
            name = subagent.get("name", f"subagent-{len(subagents)}")
            description = subagent.get("description", f"Subagent for {parent_agent}")
            
            # 创建子代理目录
            subagent_dir = self.subagents_dir / name
            subagent_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建子代理配置
            subagent_config = {
                "name": name,
                "version": "1.0.0",
                "description": description,
                "parent_agent": parent_agent,
                "model": {"name": "deepseek-chat", "temperature": 0.7},
                "tools": ["read", "write", "edit", "bash", "glob", "grep"],
            }
            
            # 保存子代理配置
            subagent_yaml_path = subagent_dir / "agent.yaml"
            with open(subagent_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(subagent_config, f, allow_unicode=True, default_flow_style=False)
            
            print(f"子代理 {name} 配置已保存到 {subagent_yaml_path}")
    
    def import_github_repo(self, github_url: str, agent_name: Optional[str] = None) -> bool:
        """主导入函数"""
        print(f"开始导入 GitHub 仓库: {github_url}")
        
        # 解析 URL
        owner, repo = self.parse_github_url(github_url)
        if not owner or not repo:
            print(f"无法解析 GitHub URL: {github_url}")
            return False
        
        print(f"解析结果: owner={owner}, repo={repo}")
        
        # 设置 agent 名称
        if not agent_name:
            agent_name = repo.replace("-", "_").lower()
        
        # 克隆仓库
        local_path = self.git_clone(owner, repo)
        if not local_path:
            print("克隆失败，尝试使用 API 方式...")
            # 这里可以添加 API 方式获取文件的逻辑
            return False
        
        # 分析项目结构
        print("分析项目结构...")
        structure = self.analyze_project_structure(local_path)
        
        # 打印分析结果
        print(f"项目分析结果:")
        print(f"  - 包含 CLAUDE.md: {structure['has_claude_md']}")
        print(f"  - 包含 AGENTS.md: {structure['has_agents_md']}")
        print(f"  - 包含 Skills: {structure['has_skills']} ({len(structure['skills'])}个)")
        print(f"  - 包含 MCPs: {structure['has_mcps']} ({len(structure['mcps'])}个)")
        print(f"  - 包含 Hooks: {structure['has_hooks']} ({len(structure['hooks'])}个)")
        print(f"  - 包含 Evaluations: {structure['has_evaluation']} ({len(structure['evaluations'])}个)")
        print(f"  - 子代理数量: {len(structure['subagent_prompts'])}")
        
        # 创建 Agent 配置
        print(f"创建 Agent 配置: {agent_name}")
        success = self.create_agent_config(owner, repo, agent_name, structure, local_path)
        
        if success:
            print(f"\n✅ 成功导入 GitHub 仓库 {owner}/{repo} 作为 Agent: {agent_name}")
            print(f"Agent 配置位置: packages/{agent_name}/agent.yaml")
            print(f"原始仓库位置: packages/{agent_name}/original/")
            print(f"子代理位置: subagents/")
            return True
        else:
            print(f"\n❌ 导入失败")
            return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python github_import_script.py <github_url> [agent_name]")
        print("示例: python github_import_script.py https://github.com/affaan-m/everything-claude-code my-agent")
        print("示例: python github_import_script.py affaan-m/everything-claude-code")
        return
    
    github_url = sys.argv[1]
    agent_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    importer = GitHubAgentImporter()
    success = importer.import_github_repo(github_url, agent_name)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()