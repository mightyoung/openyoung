"use client";

import { motion } from "framer-motion";
import { Bot, MessageSquare, FolderOpen, BarChart3, Settings, Sparkles } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { GradientBackground } from "@/components/ui/gradient-bg";
import { useLanguage } from "@/components/language-provider";

const features = [
  { key: "agents", icon: Bot, href: "/agents", color: "purple" },
  { key: "chat", icon: MessageSquare, href: "/chat", color: "cyan" },
  { key: "sessions", icon: FolderOpen, href: "/sessions", color: "green" },
  { key: "dashboard", icon: BarChart3, href: "/dashboard", color: "orange" },
  { key: "settings", icon: Settings, href: "/settings", color: "pink" },
];

const colorMap = {
  purple: {
    bg: "bg-indigo-500/10",
    text: "text-indigo-500",
    border: "border-indigo-500/20",
    hover: "hover:border-indigo-500/40 hover:shadow-indigo-500/20",
  },
  cyan: {
    bg: "bg-sky-500/10",
    text: "text-sky-500",
    border: "border-sky-500/20",
    hover: "hover:border-sky-500/40 hover:shadow-sky-500/20",
  },
  green: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-500",
    border: "border-emerald-500/20",
    hover: "hover:border-emerald-500/40 hover:shadow-emerald-500/20",
  },
  orange: {
    bg: "bg-amber-500/10",
    text: "text-amber-500",
    border: "border-amber-500/20",
    hover: "hover:border-amber-500/40 hover:shadow-amber-500/20",
  },
  pink: {
    bg: "bg-rose-500/10",
    text: "text-rose-500",
    border: "border-rose-500/20",
    hover: "hover:border-rose-500/40 hover:shadow-rose-500/20",
  },
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
  },
};

export default function HomePage() {
  const { t } = useLanguage();

  return (
    <GradientBackground>
      <div className="min-h-screen p-8 relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              {t("home.title")}
            </h1>
          </div>
          <p className="text-muted-foreground text-lg">
            {t("home.subtitle")}
          </p>
        </motion.div>

        {/* Quick Start */}
        <motion.section
          className="mb-12"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.h2
            className="text-xl font-semibold mb-6"
            variants={itemVariants}
          >
            {t("home.quickStart")}
          </motion.h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              const colors = colorMap[feature.color as keyof typeof colorMap];
              return (
                <motion.div key={feature.href} variants={itemVariants}>
                  <Link href={feature.href}>
                    <Card className={`group cursor-pointer transition-all duration-300 hover:shadow-lg ${colors.hover} border ${colors.border} bg-card overflow-hidden`}>
                      <CardContent className="p-6 relative">
                        <div className="flex items-start gap-4">
                          <motion.div
                            className={`p-3 rounded-xl ${colors.bg} transition-transform group-hover:scale-110`}
                            whileHover={{ rotate: 5 }}
                            transition={{ type: "spring", stiffness: 300, damping: 10 }}
                          >
                            <Icon className={`h-6 w-6 ${colors.text}`} />
                          </motion.div>
                          <div className="flex-1">
                            <h3 className={`font-semibold ${colors.text} group-hover:transition-colors`}>
                              {t("feature." + feature.key)}
                            </h3>
                            <p className="text-sm text-muted-foreground mt-1">
                              {t("feature." + feature.key + "Desc")}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </motion.section>

        {/* Getting Started Guide */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <h2 className="text-xl font-semibold mb-6">{t("home.gettingStarted")}</h2>
          <Card className="bg-card border-border">
            <CardContent className="p-6">
              <ol className="space-y-4">
                {[
                  { step: 1, titleKey: "home.step1", descKey: "home.step1Desc" },
                  { step: 2, titleKey: "home.step2", descKey: "home.step2Desc" },
                  { step: 3, titleKey: "home.step3", descKey: "home.step3Desc" },
                  { step: 4, titleKey: "home.step4", descKey: "home.step4Desc" },
                ].map((item, index) => (
                  <motion.li
                    key={item.step}
                    className="flex gap-3"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                  >
                    <span
                      className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary border border-primary/20"
                    >
                      {item.step}
                    </span>
                    <div>
                      <p className="font-medium">{t(item.titleKey)}</p>
                      <p className="text-sm text-muted-foreground">
                        {t(item.descKey)}
                      </p>
                    </div>
                  </motion.li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </motion.section>
      </div>
    </GradientBackground>
  );
}
