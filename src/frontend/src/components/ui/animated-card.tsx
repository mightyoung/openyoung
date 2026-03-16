"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface AnimatedCardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  delay?: number;
}

export function AnimatedCard({ children, className, hoverable = true, delay = 0 }: AnimatedCardProps) {
  return (
    <motion.div
      className={cn("rounded-xl border border-border bg-card", className)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay,
        ease: [0.25, 0.1, 0.25, 1],
      }}
      whileHover={hoverable ? { scale: 1.02, y: -2 } : undefined}
      whileTap={hoverable ? { scale: 0.99 } : undefined}
    >
      {children}
    </motion.div>
  );
}

interface AnimatedCardHeaderProps {
  children: ReactNode;
  className?: string;
}

export function AnimatedCardHeader({ children, className }: AnimatedCardHeaderProps) {
  return (
    <motion.div
      className={cn("p-6 pb-0", className)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.1, duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}

interface AnimatedCardContentProps {
  children: ReactNode;
  className?: string;
}

export function AnimatedCardContent({ children, className }: AnimatedCardContentProps) {
  return (
    <motion.div
      className={cn("p-6", className)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2, duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}
