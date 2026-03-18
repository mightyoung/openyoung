"""
Skills Page - 技能管理页面
支持浏览、创建、安装/卸载 Skills
"""

import streamlit as st

# 页面配置
st.set_page_config(page_title="Skills", page_icon="🛠️", layout="wide")

# 导入服务
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from webui.utils.config import config
from skills.registry import SkillRegistry
from skills.loader import SkillLoader
from pathlib import Path


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title(f"{config.PAGE_ICON} OpenYoung")
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Agents.py", label="🤖 Agents")
        st.page_link("pages/2_Chat.py", label="💬 Chat")
        st.page_link("pages/3_Sessions.py", label="📋 Sessions")
        st.page_link("pages/4_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/5_Settings.py", label="⚙️ Settings")


def load_skills() -> list:
    """加载Skills列表"""
    # 使用SkillRegistry加载
    registry = SkillRegistry()
    registry.load()

    skills = registry.list_all()

    # 如果没有，从loader获取
    if not skills:
        loader = SkillLoader()
        # 同步获取 - 简单实现
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_yaml = skill_dir / "skill.yaml"
                    if skill_yaml.exists():
                        skills.append({
                            "name": skill_dir.name,
                            "source": "local",
                            "file_path": str(skill_yaml)
                        })

    return skills


def render_skill_list(skills: list):
    """渲染技能列表"""
    if not skills:
        st.info("No skills found. Create or install one to get started.")
        return

    # 搜索过滤
    search_query = st.text_input("🔍 Search skills...", placeholder="Type to filter...")

    # 过滤
    filtered = skills
    if search_query:
        query = search_query.lower()
        filtered = [s for s in skills if query in str(s.get("name", "")).lower() or
                   query in str(s.get("description", "")).lower()]

    # 显示
    for skill in filtered:
        name = skill.get("name", "Unknown")
        description = skill.get("description", "No description")
        source = skill.get("source", "local")

        with st.expander(f"📦 {name}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Description**: {description}")
                st.caption(f"Source: {source}")

            with col2:
                if source == "local":
                    st.button("🗑️ Uninstall", key=f"uninstall_{name}")
                else:
                    st.button("⬇️ Install", key=f"install_{name}")


def render_create_skill():
    """渲染创建技能表单"""
    st.header("➕ Create New Skill")

    with st.form("create_skill"):
        name = st.text_input("Skill Name", placeholder="my-awesome-skill")
        description = st.text_area("Description", placeholder="What does this skill do?")
        tags = st.text_input("Tags (comma-separated)", placeholder="web, api, utility")

        submitted = st.form_submit_button("Create Skill")

        if submitted:
            if name:
                st.success(f"Skill '{name}' created successfully! (demo)")
            else:
                st.error("Please enter a skill name")


def main():
    """主函数"""
    st.title("🛠️ Skills")

    render_sidebar()

    # Tab切换
    tab1, tab2 = st.tabs(["📋 Browse Skills", "➕ Create New"])

    with tab1:
        skills = load_skills()
        render_skill_list(skills)

    with tab2:
        render_create_skill()


if __name__ == "__main__":
    main()
