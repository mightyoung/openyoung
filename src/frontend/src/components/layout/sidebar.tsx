"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import {
  Home,
  Bot,
  MessageSquare,
  FolderOpen,
  BarChart3,
  Settings,
  Sparkles,
  Menu,
  X,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useLanguage } from "@/components/language-provider";

const navItems = [
  { href: "/", labelKey: "nav.home", icon: Home },
  { href: "/agents", labelKey: "nav.agents", icon: Bot },
  { href: "/chat", labelKey: "nav.chat", icon: MessageSquare },
  { href: "/sessions", labelKey: "nav.sessions", icon: FolderOpen },
  { href: "/dashboard", labelKey: "nav.dashboard", icon: BarChart3 },
  { href: "/settings", labelKey: "nav.settings", icon: Settings },
];

const sidebarVariants: Variants = {
  open: { x: 0 },
  closed: { x: "-100%" },
};

const mobileNavItemVariants: Variants = {
  open: {
    opacity: 1,
    x: 0,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
  closed: {
    opacity: 0,
    x: -20,
    transition: {
      staggerChildren: 0.02,
      staggerDirection: -1,
    },
  },
};

const itemVariants = {
  open: { opacity: 1, x: 0 },
  closed: { opacity: 0, x: -10 },
};

export function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const { language, setLanguage, t } = useLanguage();

  const toggleLanguage = () => {
    setLanguage(language === "en" ? "zh" : "en");
  };

  return (
    <>
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 h-14 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-full items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <span className="font-semibold text-foreground">OpenYoung</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </header>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Mobile Sidebar */}
      <motion.aside
        className="fixed left-0 top-0 z-50 h-screen w-64 border-r border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:hidden"
        variants={sidebarVariants}
        initial="closed"
        animate={isOpen ? "open" : "closed"}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-14 items-center gap-2 border-b border-border/50 px-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <span className="font-semibold text-foreground">OpenYoung</span>
          </div>

          {/* Navigation */}
          <motion.nav
            className="flex-1 space-y-1 p-3"
            variants={mobileNavItemVariants}
            initial="closed"
            animate={isOpen ? "open" : "closed"}
          >
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                >
                  <motion.div
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                    variants={itemVariants}
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Icon
                      className={cn("h-4 w-4", isActive && "text-primary")}
                    />
                    {t(item.labelKey)}
                  </motion.div>
                </Link>
              );
            })}
          </motion.nav>

          {/* Bottom section */}
          <div className="border-t border-border/50 p-3">
            <Separator className="mb-3" />
            <div className="space-y-2">
              <Button
                variant="ghost"
                className="w-full justify-start"
                onClick={() => {
                  toggleLanguage();
                  setIsOpen(false);
                }}
              >
                <Globe className="h-4 w-4 mr-2" />
                {language === "en" ? "中文" : "English"}
              </Button>
              <Link href="/settings" onClick={() => setIsOpen(false)}>
                <motion.div
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Settings className="h-4 w-4" />
                  {language === "en" ? "Settings" : "设置"}
                </motion.div>
              </Link>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:fixed lg:left-0 lg:top-0 lg:z-40 lg:h-screen lg:w-64 lg:block lg:border-r lg:border-border/50 lg:bg-background/95 lg:backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-14 items-center gap-2 border-b border-border/50 px-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <span className="font-semibold text-foreground">OpenYoung</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-3">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon
                    className={cn("h-4 w-4", isActive && "text-primary")}
                  />
                  {t(item.labelKey)}
                </Link>
              );
            })}
          </nav>

          {/* Bottom section */}
          <div className="border-t border-border/50 p-3">
            <Separator className="mb-3" />
            <div className="space-y-2">
              <Button
                variant="ghost"
                className="w-full justify-start text-left"
                onClick={toggleLanguage}
              >
                <Globe className="h-4 w-4 mr-2" />
                {language === "en" ? "中文" : "English"}
              </Button>
              <Link href="/settings" className="block">
                <Button variant="ghost" className="w-full justify-start text-left">
                  <Settings className="h-4 w-4 mr-2" />
                  {language === "en" ? "Settings" : "设置"}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
