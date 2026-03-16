"use client";

import { motion } from "framer-motion";
import { Home, Search, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <motion.div
        className="max-w-md w-full text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <motion.div
          className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-500/20 to-cyan-500/20 flex items-center justify-center"
          animate={{
            boxShadow: [
              "0 0 20px rgba(139, 92, 246, 0.2)",
              "0 0 40px rgba(139, 92, 246, 0.4)",
              "0 0 20px rgba(139, 92, 246, 0.2)",
            ],
          }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          <AlertCircle className="h-12 w-12 text-purple-400" />
        </motion.div>

        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent mb-2">
          404
        </h1>
        <h2 className="text-xl font-semibold mb-2">Page Not Found</h2>
        <p className="text-muted-foreground mb-6">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>

        <div className="flex gap-3 justify-center">
          <Link href="/">
            <Button>
              <Home className="mr-2 h-4 w-4" />
              Go Home
            </Button>
          </Link>
          <Link href="/agents">
            <Button variant="outline">
              <Search className="mr-2 h-4 w-4" />
              Browse Agents
            </Button>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
