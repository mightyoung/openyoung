"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  color?: "purple" | "cyan" | "green" | "red" | "orange";
  delay?: number;
}

const colorMap = {
  purple: {
    bg: "bg-purple-500/10",
    text: "text-purple-500",
    glow: "hover:shadow-purple-500/20",
  },
  cyan: {
    bg: "bg-cyan-500/10",
    text: "text-cyan-500",
    glow: "hover:shadow-cyan-500/20",
  },
  green: {
    bg: "bg-green-500/10",
    text: "text-green-500",
    glow: "hover:shadow-green-500/20",
  },
  red: {
    bg: "bg-red-500/10",
    text: "text-red-500",
    glow: "hover:shadow-red-500/20",
  },
  orange: {
    bg: "bg-orange-500/10",
    text: "text-orange-500",
    glow: "hover:shadow-orange-500/20",
  },
};

export function StatCard({ title, value, subtitle, icon, color = "purple", delay = 0 }: StatCardProps) {
  const colors = colorMap[color];

  return (
    <motion.div
      className={cn(
        "rounded-xl border border-border bg-card p-6 transition-all duration-300 hover:shadow-lg",
        colors.glow
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay,
        ease: [0.25, 0.1, 0.25, 1],
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <motion.p
            className={cn("text-3xl font-bold mt-1", colors.text)}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: delay + 0.2, duration: 0.3 }}
          >
            {value}
          </motion.p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        <motion.div
          className={cn("p-3 rounded-xl", colors.bg)}
          whileHover={{ scale: 1.1, rotate: 5 }}
          transition={{ type: "spring", stiffness: 400, damping: 10 }}
        >
          {icon}
        </motion.div>
      </div>
    </motion.div>
  );
}
