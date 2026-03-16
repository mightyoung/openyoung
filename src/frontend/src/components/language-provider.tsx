"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type Language = "en" | "zh";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const translations = {
  // Navigation
  "nav.home": { en: "Home", zh: "首页" },
  "nav.agents": { en: "Agents", zh: "智能体" },
  "nav.chat": { en: "Chat", zh: "对话" },
  "nav.sessions": { en: "Sessions", zh: "会话" },
  "nav.dashboard": { en: "Dashboard", zh: "仪表盘" },
  "nav.settings": { en: "Settings", zh: "设置" },

  // Home page
  "home.title": { en: "Welcome to OpenYoung", zh: "欢迎使用 OpenYoung" },
  "home.subtitle": { en: "AI Agent with multi-platform messaging support", zh: "多平台消息支持的AI智能体" },
  "home.quickStart": { en: "Quick Start", zh: "快速开始" },
  "home.gettingStarted": { en: "Getting Started", zh: "开始使用" },
  "home.step1": { en: "Configure API Settings", zh: "配置 API 设置" },
  "home.step1Desc": { en: "Go to Settings and configure your API base URL and key", zh: "进入设置页面，配置您的 API 基础 URL 和密钥" },
  "home.step2": { en: "Browse Agents", zh: "浏览智能体" },
  "home.step2Desc": { en: "Explore available AI Agents in the Agents page", zh: "在智能体页面浏览可用的 AI 智能体" },
  "home.step3": { en: "Start Chatting", zh: "开始对话" },
  "home.step3Desc": { en: "Select an agent and start a conversation", zh: "选择一个智能体并开始对话" },
  "home.step4": { en: "Monitor Performance", zh: "监控性能" },
  "home.step4Desc": { en: "Track evaluations and execution metrics in Dashboard", zh: "在仪表盘页面跟踪评估和执行指标" },

  // Features
  "feature.agents": { en: "Agents", zh: "智能体" },
  "feature.agentsDesc": { en: "Browse and manage AI agents", zh: "浏览和管理 AI 智能体" },
  "feature.chat": { en: "Chat", zh: "对话" },
  "feature.chatDesc": { en: "Chat with AI Agents", zh: "与 AI 智能体对话" },
  "feature.sessions": { en: "Sessions", zh: "会话" },
  "feature.sessionsDesc": { en: "View conversation history", zh: "查看对话历史" },
  "feature.dashboard": { en: "Dashboard", zh: "仪表盘" },
  "feature.dashboardDesc": { en: "Track performance metrics", zh: "跟踪性能指标" },
  "feature.settings": { en: "Settings", zh: "设置" },
  "feature.settingsDesc": { en: "Configure API and preferences", zh: "配置 API 和首选项" },

  // Chat page
  "chat.title": { en: "Chat", zh: "对话" },
  "chat.subtitle": { en: "Chat with AI Agents", zh: "与AI智能体对话" },
  "chat.selectAgent": { en: "Select an Agent", zh: "选择智能体" },
  "chat.startConversation": { en: "Start a conversation", zh: "开始对话" },
  "chat.with": { en: "with", zh: "与" },
  "chat.clear": { en: "Clear", zh: "清空" },
  "chat.placeholder": { en: "Type your message...", zh: "输入消息..." },
  "chat.send": { en: "Send", zh: "发送" },
  "chat.agents": { en: "Agents", zh: "智能体" },
  "chat.loading": { en: "Loading...", zh: "加载中..." },
  "chat.receivedMessage": { en: "I received your message.", zh: "我已收到您的消息。" },
  "chat.errorMessage": { en: "Sorry, I encountered an error. Please try again.", zh: "抱歉，遇到错误，请重试。" },

  // Settings
  "settings.title": { en: "Settings", zh: "设置" },
  "settings.subtitle": { en: "Configure API connection and application preferences", zh: "配置 API 连接和应用程序首选项" },
  "settings.api": { en: "API Settings", zh: "API 设置" },
  "settings.apiDesc": { en: "Configure your API connection", zh: "配置您的 API 连接" },
  "settings.baseUrl": { en: "Base URL", zh: "基础 URL" },
  "settings.baseUrlDesc": { en: "The base URL for the API server", zh: "API 服务器的基础 URL" },
  "settings.apiKey": { en: "API Key", zh: "API 密钥" },
  "settings.apiKeyDesc": { en: "Your API key for authentication", zh: "用于认证的 API 密钥" },
  "settings.model": { en: "Model", zh: "模型" },
  "settings.modelDesc": { en: "The AI model to use", zh: "要使用的 AI 模型" },
  "settings.save": { en: "Save", zh: "保存" },
  "settings.saveApi": { en: "Save API Settings", zh: "保存 API 设置" },
  "settings.saving": { en: "Saving...", zh: "保存中..." },
  "settings.reset": { en: "Reset", zh: "重置" },
  "settings.appSettings": { en: "Application Settings", zh: "应用程序设置" },
  "settings.appDesc": { en: "Customize your experience", zh: "自定义您的体验" },
  "settings.theme": { en: "Theme", zh: "主题" },
  "settings.themeDesc": { en: "Choose your preferred color scheme", zh: "选择您喜欢的配色方案" },
  "settings.language": { en: "Language", zh: "语言" },
  "settings.languageDesc": { en: "Interface language", zh: "界面语言" },
  "settings.notifications": { en: "Notifications", zh: "通知" },
  "settings.notificationsDesc": { en: "Enable desktop notifications", zh: "启用桌面通知" },
  "settings.autosave": { en: "Auto-save", zh: "自动保存" },
  "settings.autosaveDesc": { en: "Automatically save chat sessions", zh: "自动保存对话会话" },
  "settings.saveApp": { en: "Save App Settings", zh: "保存应用设置" },
  "settings.saved": { en: "Settings saved successfully!", zh: "设置保存成功！" },
  "settings.error": { en: "Failed to save settings", zh: "保存设置失败" },
  "settings.about": { en: "About OpenYoung", zh: "关于 OpenYoung" },
  "settings.version": { en: "Version", zh: "版本" },
  "settings.frontend": { en: "Frontend", zh: "前端" },
  "settings.uiLibrary": { en: "UI Library", zh: "UI 库" },
  "settings.selectModel": { en: "Select a model", zh: "选择模型" },
  "settings.selectTheme": { en: "Select a theme", zh: "选择主题" },
  "settings.selectLanguage": { en: "Select a language", zh: "选择语言" },
  "settings.dark": { en: "Dark", zh: "深色" },
  "settings.light": { en: "Light", zh: "浅色" },
  "settings.system": { en: "System", zh: "系统" },

  // Agents page
  "agents.title": { en: "Available Agents", zh: "可用智能体" },
  "agents.subtitle": { en: "Browse and search available AI Agents", zh: "浏览和搜索可用的 AI 智能体" },
  "agents.search": { en: "Search agents...", zh: "搜索智能体..." },
  "agents.error": { en: "Failed to load agents", zh: "加载智能体失败" },
  "agents.noResults": { en: "No agents found", zh: "未找到智能体" },
  "agents.noAgents": { en: "No agents available", zh: "暂无可用智能体" },
  "agents.noDescription": { en: "No description", zh: "暂无描述" },
  "agents.startChat": { en: "Start Chat", zh: "开始对话" },

  // Sessions page
  "sessions.title": { en: "Sessions", zh: "会话" },
  "sessions.subtitle": { en: "Manage and view session history", zh: "管理和查看会话历史" },
  "sessions.error": { en: "Failed to load sessions", zh: "加载会话失败" },
  "sessions.noSessions": { en: "No sessions yet", zh: "暂无会话" },
  "sessions.startChat": { en: "Start a chat to create your first session", zh: "开始对话以创建您的第一个会话" },
  "sessions.startChatting": { en: "Start Chatting", zh: "开始对话" },
  "sessions.continueChat": { en: "Continue Chat", zh: "继续对话" },
  "sessions.messages": { en: "messages", zh: "条消息" },
  "sessions.unknown": { en: "Unknown", zh: "未知" },
  "sessions.completed": { en: "Completed", zh: "已完成" },
  "sessions.running": { en: "Running", zh: "运行中" },
  "sessions.failed": { en: "Failed", zh: "失败" },

  // Dashboard page
  "dashboard.title": { en: "Dashboard", zh: "仪表盘" },
  "dashboard.subtitle": { en: "View evaluation and execution data", zh: "查看评估和执行数据" },
  "dashboard.totalEvaluations": { en: "Total Evaluations", zh: "总评估数" },
  "dashboard.passRate": { en: "pass rate", zh: "通过率" },
  "dashboard.noEvaluations": { en: "No evaluations yet", zh: "暂无评估" },
  "dashboard.passed": { en: "Passed", zh: "已通过" },
  "dashboard.successfulEvaluations": { en: "Successful evaluations", zh: "成功的评估" },
  "dashboard.failed": { en: "Failed", zh: "失败" },
  "dashboard.failedEvaluations": { en: "Failed evaluations", zh: "失败的评估" },
  "dashboard.activeExecutions": { en: "Active Executions", zh: "活跃执行" },
  "dashboard.completed": { en: "completed", zh: "已完成" },
  "dashboard.overview": { en: "Overview", zh: "概览" },
  "dashboard.evaluations": { en: "Evaluations", zh: "评估" },
  "dashboard.executions": { en: "Executions", zh: "执行" },
  "dashboard.scoreTrend": { en: "Score Trend", zh: "分数趋势" },
  "dashboard.recentScores": { en: "Recent evaluation scores", zh: "最近的评估分数" },
  "dashboard.passFail": { en: "Pass/Fail Distribution", zh: "通过/失败分布" },
  "dashboard.evaluationResults": { en: "Evaluation results breakdown", zh: "评估结果分布" },
  "dashboard.noData": { en: "No data available", zh: "暂无数据" },
  "dashboard.scoreDistribution": { en: "Score Distribution", zh: "分数分布" },
  "dashboard.scoresByRange": { en: "Evaluation scores by range", zh: "按范围划分的评估分数" },
  "dashboard.recentEvals": { en: "Recent Evaluations", zh: "最近评估" },
  "dashboard.latestResults": { en: "Latest evaluation results", zh: "最新评估结果" },
  "dashboard.executionStatus": { en: "Execution Status", zh: "执行状态" },
  "dashboard.currentStates": { en: "Current execution states", zh: "当前执行状态" },
  "dashboard.recentExecs": { en: "Recent Executions", zh: "最近执行" },
  "dashboard.latestExecs": { en: "Latest execution results", zh: "最新执行结果" },
  "dashboard.noExecs": { en: "No executions yet", zh: "暂无执行" },
  "dashboard.test": { en: "Test", zh: "测试" },
  "dashboard.error": { en: "Failed to load dashboard data", zh: "加载仪表盘数据失败" },

  // Common
  "common.loading": { en: "Loading...", zh: "加载中..." },
  "common.error": { en: "Error", zh: "错误" },
  "common.success": { en: "Success", zh: "成功" },
  "common.cancel": { en: "Cancel", zh: "取消" },
  "common.confirm": { en: "Confirm", zh: "确认" },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    // Load from localStorage
    const saved = localStorage.getItem("language") as Language;
    if (saved && (saved === "en" || saved === "zh")) {
      setLanguageState(saved);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem("language", lang);
  };

  const t = (key: string): string => {
    const translation = translations[key as keyof typeof translations];
    if (!translation) return key;
    return translation[language] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}
