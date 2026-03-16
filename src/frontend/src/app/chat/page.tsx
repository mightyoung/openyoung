"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Loader2, MessageCircle, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { getApiClient, type Agent } from "@/lib/api";
import { useLanguage } from "@/components/language-provider";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function ChatPage() {
  const { t } = useLanguage();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadAgents = async () => {
    setLoadingAgents(true);
    try {
      const client = getApiClient();
      const data = await client.listAgents();
      setAgents(data);
      if (data.length > 0) {
        setSelectedAgent(data[0]);
      }
    } catch (err) {
      console.error("Failed to load agents:", err);
    } finally {
      setLoadingAgents(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedAgent || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const client = getApiClient();
      const response = await client.chatWithAgent(selectedAgent.id, userMessage.content);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response || t("chat.receivedMessage"),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: t("chat.errorMessage"),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="min-h-screen p-4 lg:p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 lg:mb-8"
      >
        <h1 className="text-2xl lg:text-3xl font-bold tracking-tight">{t("chat.title")}</h1>
        <p className="mt-1 lg:mt-2 text-muted-foreground">
          {t("chat.subtitle")}
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 lg:gap-6 h-[calc(100vh-8rem)] lg:h-[calc(100vh-12rem)]">
        {/* Agents Sidebar - Desktop */}
        <Card className="hidden lg:block lg:col-span-1">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{t("chat.agents")}</CardTitle>
              <Badge variant="secondary">{agents.length}</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loadingAgents ? (
              <div className="p-4 text-center text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                {t("common.loading")}
              </div>
            ) : (
              <ScrollArea className="h-[400px]">
                <div className="space-y-1 p-2">
                  {agents.map((agent) => (
                    <motion.div
                      key={agent.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Button
                        variant={selectedAgent?.id === agent.id ? "secondary" : "ghost"}
                        className="w-full justify-start text-left"
                        onClick={() => setSelectedAgent(agent)}
                      >
                        <Bot className="mr-2 h-4 w-4" />
                        <span className="truncate">{agent.name}</span>
                      </Button>
                    </motion.div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Mobile Agent Selector */}
        <div className="lg:hidden flex gap-2 overflow-x-auto pb-2">
          {agents.map((agent) => (
            <motion.button
              key={agent.id}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSelectedAgent(agent)}
              className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                selectedAgent?.id === agent.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              <Bot className="inline-block w-4 h-4 mr-1" />
              {agent.name}
            </motion.button>
          ))}
        </div>

        {/* Chat Area */}
        <Card className="lg:col-span-3 flex flex-col overflow-hidden">
          <CardHeader className="border-b py-3 lg:py-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Bot className="h-5 w-5 text-primary" />
                </motion.div>
                {selectedAgent ? selectedAgent.name : t("chat.selectAgent")}
              </CardTitle>
              {messages.length > 0 && (
                <Button variant="ghost" size="sm" onClick={clearChat}>
                  {t("chat.clear")}
                </Button>
              )}
            </div>
          </CardHeader>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4" ref={scrollRef}>
            <div className="space-y-4">
              {messages.length === 0 && (
                <motion.div
                  className="text-center text-muted-foreground py-12"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                >
                  <motion.div
                    className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center"
                  >
                    <MessageCircle className="h-8 w-8 text-primary" />
                  </motion.div>
                  <p className="text-lg font-medium">{t("chat.startConversation")}</p>
                  <p className="text-sm mt-1">
                    {t("chat.with")} {selectedAgent?.name || t("chat.selectAgent")}
                  </p>
                </motion.div>
              )}
              <AnimatePresence mode="popLayout">
                {messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    layout
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                    className={`flex gap-3 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.role === "assistant" && (
                      <motion.div
                        className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0"
                        whileHover={{ scale: 1.1, rotate: 5 }}
                      >
                        <Bot className="h-4 w-4 text-primary" />
                      </motion.div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p
                        className={`text-xs mt-1 ${
                          message.role === "user"
                            ? "text-white/70"
                            : "text-muted-foreground"
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                    {message.role === "user" && (
                      <motion.div
                        className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0"
                        whileHover={{ scale: 1.1, rotate: -5 }}
                      >
                        <User className="h-4 w-4" />
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {loading && (
                <motion.div
                  className="flex gap-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <motion.div
                    className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <Bot className="h-4 w-4 text-primary" />
                  </motion.div>
                  <div className="bg-muted rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          className="h-2 w-2 rounded-full bg-primary"
                          animate={{ y: [0, -5, 0] }}
                          transition={{
                            duration: 0.6,
                            repeat: Infinity,
                            delay: i * 0.1,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-3 lg:p-4 border-t">
            <div className="flex gap-2">
              <Input
                placeholder={t("chat.placeholder")}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={!selectedAgent || loading}
                className="bg-muted/50"
              />
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  onClick={handleSend}
                  disabled={!selectedAgent || loading || !input.trim()}
                  className="bg-primary hover:bg-primary/90"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </motion.div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
