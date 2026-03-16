"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FolderOpen, Clock, Play, CheckCircle, XCircle, Loader2, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiClient, type Session } from "@/lib/api";
import Link from "next/link";
import { useLanguage } from "@/components/language-provider";

export default function SessionsPage() {
  const { t } = useLanguage();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const client = getApiClient();
      const data = await client.listSessions();
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("sessions.error"));
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">{t("sessions.completed")}</Badge>;
      case "running":
        return <Badge className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20">{t("sessions.running")}</Badge>;
      case "failed":
        return <Badge className="bg-red-500/10 text-red-500 hover:bg-red-500/20">{t("sessions.failed")}</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen p-4 lg:p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 lg:mb-8"
      >
        <h1 className="text-2xl lg:text-3xl font-bold tracking-tight">{t("sessions.title")}</h1>
        <p className="mt-1 lg:mt-2 text-muted-foreground">
          {t("sessions.subtitle")}
        </p>
      </motion.div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Card className="mb-6 lg:mb-8 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card>
                <CardContent className="pt-6">
                  <Skeleton className="h-20 w-full" />
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Sessions List */}
      {!loading && sessions.length === 0 && (
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
                  <FolderOpen className="h-8 w-8 text-muted-foreground" />
                </motion.div>
                <p className="text-muted-foreground">{t("sessions.noSessions")}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {t("sessions.startChat")}
                </p>
                <Link href="/chat" className="mt-4 inline-block">
                  <Button className="bg-gradient-to-r from-purple-600 to-cyan-600">
                    <Sparkles className="mr-2 h-4 w-4" />
                    {t("sessions.startChatting")}
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {!loading && sessions.length > 0 && (
        <div className="space-y-4">
          <AnimatePresence mode="popLayout">
            {sessions.map((session, index) => (
              <motion.div
                key={session.session_id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card className="transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <motion.div
                          className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-cyan-500/20 flex items-center justify-center"
                          whileHover={{ scale: 1.1, rotate: 5 }}
                        >
                          <FolderOpen className="h-5 w-5 text-purple-400" />
                        </motion.div>
                        <div>
                          <CardTitle className="text-base">{session.agent_name}</CardTitle>
                          <p className="text-sm text-muted-foreground font-mono">
                            {session.session_id.slice(0, 12)}...
                          </p>
                        </div>
                      </div>
                      {getStatusBadge(session.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {session.created_at ? new Date(session.created_at).toLocaleString() : t("sessions.unknown")}
                      </div>
                      {session.message_count !== undefined && (
                        <div className="flex items-center gap-1">
                          <Play className="h-4 w-4" />
                          {session.message_count} {t("sessions.messages")}
                        </div>
                      )}
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Link href={`/chat?session=${session.session_id}`}>
                        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                          <Button variant="outline" size="sm">
                            {t("sessions.continueChat")}
                          </Button>
                        </motion.div>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
