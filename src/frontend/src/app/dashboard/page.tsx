"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, CheckCircle, XCircle, Clock, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatCard } from "@/components/ui/stat-card";
import { getApiClient, type Evaluation, type Execution } from "@/lib/api";
import { useLanguage } from "@/components/language-provider";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";

const COLORS = ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];

interface DashboardStats {
  totalEvaluations: number;
  passedEvaluations: number;
  failedEvaluations: number;
  passRate: number;
  totalExecutions: number;
  runningExecutions: number;
  completedExecutions: number;
  failedExecutions: number;
}

export default function DashboardPage() {
  const { t } = useLanguage();
  const [stats, setStats] = useState<DashboardStats>({
    totalEvaluations: 0,
    passedEvaluations: 0,
    failedEvaluations: 0,
    passRate: 0,
    totalExecutions: 0,
    runningExecutions: 0,
    completedExecutions: 0,
    failedExecutions: 0,
  });
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const client = getApiClient();
      const [evalResponse, execResponse] = await Promise.all([
        client.listEvaluations(),
        client.listExecutions({}),
      ]);

      const evalData = evalResponse.items || evalResponse;
      const execData = execResponse.items || execResponse;

      setEvaluations(evalData);
      setExecutions(execData);

      const passed = evalData.filter((e) => e.passed).length;
      const failed = evalData.filter((e) => !e.passed).length;

      setStats({
        totalEvaluations: evalData.length,
        passedEvaluations: passed,
        failedEvaluations: failed,
        passRate: evalData.length > 0 ? (passed / evalData.length) * 100 : 0,
        totalExecutions: execData.length,
        runningExecutions: execData.filter((e) => e.status === "running").length,
        completedExecutions: execData.filter((e) => e.status === "completed").length,
        failedExecutions: execData.filter((e) => e.status === "failed").length,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("dashboard.error"));
    } finally {
      setLoading(false);
    }
  };

  const scoreDistribution = evaluations.reduce((acc, eval_) => {
    const score = Math.floor(eval_.overall_score / 20) * 20;
    const label = `${score}-${score + 20}%`;
    const existing = acc.find((item) => item.name === label);
    if (existing) {
      existing.value += 1;
    } else {
      acc.push({ name: label, value: 1 });
    }
    return acc;
  }, [] as { name: string; value: number }[]);

  const trendData = evaluations.slice(-10).map((eval_, index) => ({
    name: `Eval ${index + 1}`,
    score: eval_.overall_score * 100,
    passed: eval_.passed ? 1 : 0,
  }));

  const executionStatusData = [
    { name: "Completed", value: stats.completedExecutions },
    { name: "Running", value: stats.runningExecutions },
    { name: "Failed", value: stats.failedExecutions },
  ].filter((d) => d.value > 0);

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">{t("dashboard.title")}</h1>
          <p className="mt-2 text-muted-foreground">
            {t("dashboard.subtitle")}
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-20 animate-pulse bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold tracking-tight">{t("dashboard.title")}</h1>
        <p className="mt-2 text-muted-foreground">
          {t("dashboard.subtitle")}
        </p>
      </motion.div>

      {error && (
        <Card className="mb-8 border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <motion.div
        className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <StatCard
          title={t("dashboard.totalEvaluations")}
          value={stats.totalEvaluations}
          subtitle={stats.totalEvaluations > 0 ? `${stats.passRate.toFixed(1)}% ${t("dashboard.passRate")}` : t("dashboard.noEvaluations")}
          icon={<BarChart3 className="h-6 w-6 text-purple-500" />}
          color="purple"
          delay={0}
        />
        <StatCard
          title={t("dashboard.passed")}
          value={stats.passedEvaluations}
          subtitle={t("dashboard.successfulEvaluations")}
          icon={<CheckCircle className="h-6 w-6 text-green-500" />}
          color="green"
          delay={0.1}
        />
        <StatCard
          title={t("dashboard.failed")}
          value={stats.failedEvaluations}
          subtitle={t("dashboard.failedEvaluations")}
          icon={<XCircle className="h-6 w-6 text-red-500" />}
          color="red"
          delay={0.2}
        />
        <StatCard
          title={t("dashboard.activeExecutions")}
          value={stats.runningExecutions}
          subtitle={`${stats.completedExecutions} ${t("dashboard.completed")}`}
          icon={<Activity className="h-6 w-6 text-cyan-500" />}
          color="cyan"
          delay={0.3}
        />
      </motion.div>

      {/* Charts */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">{t("dashboard.overview")}</TabsTrigger>
          <TabsTrigger value="evaluations">{t("dashboard.evaluations")}</TabsTrigger>
          <TabsTrigger value="executions">{t("dashboard.executions")}</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("dashboard.scoreTrend")}</CardTitle>
                  <CardDescription>{t("dashboard.recentScores")}</CardDescription>
                </CardHeader>
                <CardContent>
                  {trendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={trendData}>
                        <defs>
                          <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="name" className="text-xs" />
                        <YAxis className="text-xs" domain={[0, 100]} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="score"
                          stroke="#8b5cf6"
                          fill="url(#scoreGradient)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      {t("dashboard.noData")}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("dashboard.passFail")}</CardTitle>
                  <CardDescription>{t("dashboard.evaluationResults")}</CardDescription>
                </CardHeader>
                <CardContent>
                  {stats.totalEvaluations > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: "Passed", value: stats.passedEvaluations },
                            { name: "Failed", value: stats.failedEvaluations },
                          ].filter((d) => d.value > 0)}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {[0, 1].map((_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={index === 0 ? "#10b981" : "#ef4444"}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      {t("dashboard.noData")}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </TabsContent>

        <TabsContent value="evaluations" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("dashboard.scoreDistribution")}</CardTitle>
                  <CardDescription>{t("dashboard.scoresByRange")}</CardDescription>
                </CardHeader>
                <CardContent>
                  {scoreDistribution.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={scoreDistribution}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="name" className="text-xs" />
                        <YAxis className="text-xs" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                          }}
                        />
                        <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      {t("dashboard.noEvaluations")}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("dashboard.recentEvals")}</CardTitle>
                  <CardDescription>{t("dashboard.latestResults")}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {evaluations.slice(0, 5).map((eval_, index) => (
                      <motion.div
                        key={eval_.id || index}
                        className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 * index }}
                      >
                        <div className="flex items-center gap-2">
                          {eval_.passed ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span className="text-sm font-medium">
                            Test {index + 1}
                          </span>
                        </div>
                        <span className="text-sm font-mono">
                          {(eval_.overall_score * 100).toFixed(0)}%
                        </span>
                      </motion.div>
                    ))}
                    {evaluations.length === 0 && (
                      <p className="text-center text-muted-foreground py-8">
                        {t("dashboard.noEvaluations")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("dashboard.executionStatus")}</CardTitle>
                  <CardDescription>{t("dashboard.currentStates")}</CardDescription>
                </CardHeader>
                <CardContent>
                  {executionStatusData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={executionStatusData}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, percent }) =>
                            `${name} ${(percent * 100).toFixed(0)}%`
                          }
                        >
                          {executionStatusData.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      {t("dashboard.noExecs")}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("dashboard.recentExecs")}</CardTitle>
                  <CardDescription>{t("dashboard.latestExecs")}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {executions.slice(0, 5).map((exec, index) => (
                      <motion.div
                        key={exec.run_id || index}
                        className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 * index }}
                      >
                        <div className="flex items-center gap-2">
                          {exec.status === "completed" ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : exec.status === "running" ? (
                            <Clock className="h-4 w-4 text-blue-500 animate-pulse" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span className="text-sm font-medium truncate">
                            {exec.agent_name}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground font-mono">
                          {exec.run_id?.slice(0, 8)}...
                        </span>
                      </motion.div>
                    ))}
                    {executions.length === 0 && (
                      <p className="text-center text-muted-foreground py-8">
                        {t("dashboard.noExecs")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
