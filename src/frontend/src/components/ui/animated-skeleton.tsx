"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnimatedSkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
}

export function AnimatedSkeleton({ className, variant = "rectangular" }: AnimatedSkeletonProps) {
  const baseStyles = "bg-gradient-to-r from-muted via-muted/70 to-muted bg-[length:200%_100%]";

  const variants = {
    text: "h-4 rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  return (
    <motion.div
      className={cn(baseStyles, variants[variant], className)}
      animate={{
        backgroundPosition: ["200% 0", "-200% 0"],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: "linear",
      }}
    />
  );
}

// Animated card skeleton for grid loading
export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <AnimatedSkeleton className="h-5 w-3/4 mb-4" />
      <AnimatedSkeleton className="h-4 w-full mb-2" />
      <AnimatedSkeleton className="h-4 w-2/3" />
    </div>
  );
}

// Animated list skeleton
export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <AnimatedSkeleton variant="circular" className="h-10 w-10" />
          <div className="flex-1 space-y-2">
            <AnimatedSkeleton className="h-4 w-1/3" />
            <AnimatedSkeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}
