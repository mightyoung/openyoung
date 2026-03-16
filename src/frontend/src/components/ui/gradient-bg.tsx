"use client";

import { ReactNode } from "react";

interface GradientBackgroundProps {
  children: ReactNode;
}

export function GradientBackground({ children }: GradientBackgroundProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* Subtle texture for depth - minimal and professional */}
      <div className="pointer-events-none fixed inset-0 opacity-[0.02]">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 50% 50%, currentColor 1px, transparent 1px)`,
            backgroundSize: "32px 32px",
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}

// Grid pattern overlay - subtle and functional
export function GridPattern() {
  return null; // Disabled - too distracting
}
