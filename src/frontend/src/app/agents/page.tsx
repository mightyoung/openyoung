"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Search, CheckCircle, Star, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiClient, type Agent } from "@/lib/api";
import Link from "next/link";
import { useLanguage } from "@/components/language-provider";

export default function AgentsPage() {
  const { t } = useLanguage();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const client = getApiClient();
      const data = await client.listAgents(search || undefined);
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("agents.error"));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadAgents();
  };

  return (
    <div className="min-h-screen p-4 lg:p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 lg:mb-8"
      >
        <h1 className="text-2xl lg:text-3xl font-bold tracking-tight">{t("agents.title")}</h1>
        <p className="mt-1 lg:mt-2 text-muted-foreground">
          {t("agents.subtitle")}
        </p>
      </motion.div>

      {/* Search */}
      <motion.form
        onSubmit={handleSearch}
        className="mb-6 lg:mb-8"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("agents.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-muted/50"
          />
        </div>
      </motion.form>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Card className="mb-6 lg:mb-8 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{t("agents.error")}</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Loading */}
      {loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-3/4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3 mt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Agents Grid */}
      {!loading && agents.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <motion.div
                  className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center"
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Bot className="h-8 w-8 text-muted-foreground" />
                </motion.div>
                <p className="text-muted-foreground">
                  {search ? t("agents.noResults") : t("agents.noAgents")}
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {!loading && agents.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {agents.map((agent, index) => (
              <motion.div
                key={agent.id}
                layout
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Link href={`/chat?agent=${agent.id}`}>
                  <Card className="group cursor-pointer transition-all duration-300 hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-1 h-full">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <motion.div
                            className="p-2 rounded-lg bg-purple-500/10"
                            whileHover={{ rotate: 15, scale: 1.1 }}
                          >
                            <Bot className="h-4 w-4 text-purple-500" />
                          </motion.div>
                          {agent.name}
                        </CardTitle>
                        <div className="flex gap-1">
                          {agent.verified && (
                            <motion.div
                              whileHover={{ scale: 1.2 }}
                            >
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            </motion.div>
                          )}
                          {agent.top_rated && (
                            <motion.div
                              whileHover={{ scale: 1.2, rotate: 15 }}
                            >
                              <Star className="h-4 w-4 text-yellow-500" />
                            </motion.div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                        {agent.description || t("agents.noDescription")}
                      </p>
                      <div className="flex flex-wrap gap-2 mb-4">
                        {agent.tags?.slice(0, 3).map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                        <Button className="w-full bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500">
                          <Sparkles className="mr-2 h-4 w-4" />
                          {t("agents.startChat")}
                        </Button>
                      </motion.div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
