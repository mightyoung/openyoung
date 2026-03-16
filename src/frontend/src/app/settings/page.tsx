"use client";

import { useState, useEffect } from "react";
import { Settings as SettingsIcon, Save, RotateCcw, Check, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useLanguage } from "@/components/language-provider";

interface ApiSettings {
  baseUrl: string;
  apiKey: string;
  model: string;
}

interface AppSettings {
  theme: string;
  language: string;
  notifications: boolean;
  autoSave: boolean;
}

const DEFAULT_API_SETTINGS: ApiSettings = {
  baseUrl: "http://localhost:8000",
  apiKey: "",
  model: "claude-sonnet-4-20250514",
};

const DEFAULT_APP_SETTINGS: AppSettings = {
  theme: "dark",
  language: "en",
  notifications: true,
  autoSave: true,
};

export default function SettingsPage() {
  const { t } = useLanguage();
  const [apiSettings, setApiSettings] = useState<ApiSettings>(DEFAULT_API_SETTINGS);
  const [appSettings, setAppSettings] = useState<AppSettings>(DEFAULT_APP_SETTINGS);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    // Load from localStorage
    const savedApi = localStorage.getItem("openyoung_api_settings");
    const savedApp = localStorage.getItem("openyoung_app_settings");

    if (savedApi) {
      setApiSettings(JSON.parse(savedApi));
    }
    if (savedApp) {
      setAppSettings(JSON.parse(savedApp));
    }
  };

  const handleSaveApiSettings = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      // Save to localStorage
      localStorage.setItem("openyoung_api_settings", JSON.stringify(apiSettings));

      // Simulate save delay
      await new Promise((resolve) => setTimeout(resolve, 500));

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAppSettings = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      localStorage.setItem("openyoung_app_settings", JSON.stringify(appSettings));
      await new Promise((resolve) => setTimeout(resolve, 500));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleResetApiSettings = () => {
    setApiSettings(DEFAULT_API_SETTINGS);
    localStorage.removeItem("openyoung_api_settings");
  };

  const handleResetAppSettings = () => {
    setAppSettings(DEFAULT_APP_SETTINGS);
    localStorage.removeItem("openyoung_app_settings");
  };

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">{t("settings.title")}</h1>
        <p className="mt-2 text-muted-foreground">
          {t("settings.subtitle")}
        </p>
      </div>

      {/* Error */}
      {error && (
        <Card className="mb-8 border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-4 w-4" />
              <p>{t("settings.error")}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success */}
      {saved && (
        <Card className="mb-8 border-green-500/50 bg-green-500/10">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-green-500">
              <Check className="h-4 w-4" />
              <p>{t("settings.saved")}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* API Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <SettingsIcon className="h-5 w-5" />
              {t("settings.api")}
            </CardTitle>
            <CardDescription>
              {t("settings.apiDesc")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="baseUrl">{t("settings.baseUrl")}</Label>
              <Input
                id="baseUrl"
                placeholder="http://localhost:8000"
                value={apiSettings.baseUrl}
                onChange={(e) =>
                  setApiSettings({ ...apiSettings, baseUrl: e.target.value })
                }
              />
              <p className="text-xs text-muted-foreground">
                {t("settings.baseUrlDesc")}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="apiKey">{t("settings.apiKey")}</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="Enter your API key"
                value={apiSettings.apiKey}
                onChange={(e) =>
                  setApiSettings({ ...apiSettings, apiKey: e.target.value })
                }
              />
              <p className="text-xs text-muted-foreground">
                {t("settings.apiKeyDesc")}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">{t("settings.model")}</Label>
              <Select
                value={apiSettings.model || "claude-sonnet-4-20250514"}
                onValueChange={(value) =>
                  setApiSettings({ ...apiSettings, model: value || "claude-sonnet-4-20250514" })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder={t("settings.selectModel")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="claude-sonnet-4-20250514">Claude Sonnet 4</SelectItem>
                  <SelectItem value="claude-opus-4-6-20250501">Claude Opus 4.6</SelectItem>
                  <SelectItem value="claude-haiku-4-5-20251001">Claude Haiku 4.5</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t("settings.modelDesc")}
              </p>
            </div>

            <Separator />

            <div className="flex gap-2">
              <Button onClick={handleSaveApiSettings} disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? t("settings.saving") : t("settings.saveApi")}
              </Button>
              <Button variant="outline" onClick={handleResetApiSettings}>
                <RotateCcw className="mr-2 h-4 w-4" />
                {t("settings.reset")}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* App Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <SettingsIcon className="h-5 w-5" />
              {t("settings.appSettings")}
            </CardTitle>
            <CardDescription>
              {t("settings.appDesc")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theme">{t("settings.theme")}</Label>
              <Select
                value={appSettings.theme || "dark"}
                onValueChange={(value) =>
                  setAppSettings({ ...appSettings, theme: value || "dark" })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder={t("settings.selectTheme")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dark">{t("settings.dark")}</SelectItem>
                  <SelectItem value="light">{t("settings.light")}</SelectItem>
                  <SelectItem value="system">{t("settings.system")}</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t("settings.themeDesc")}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">{t("settings.language")}</Label>
              <Select
                value={appSettings.language || "en"}
                onValueChange={(value) =>
                  setAppSettings({ ...appSettings, language: value || "en" })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder={t("settings.selectLanguage")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="zh">中文</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {t("settings.languageDesc")}
              </p>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t("settings.notifications")}</Label>
                <p className="text-xs text-muted-foreground">
                  {t("settings.notificationsDesc")}
                </p>
              </div>
              <Switch
                checked={appSettings.notifications}
                onCheckedChange={(checked) =>
                  setAppSettings({ ...appSettings, notifications: checked })
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t("settings.autosave")}</Label>
                <p className="text-xs text-muted-foreground">
                  {t("settings.autosaveDesc")}
                </p>
              </div>
              <Switch
                checked={appSettings.autoSave}
                onCheckedChange={(checked) =>
                  setAppSettings({ ...appSettings, autoSave: checked })
                }
              />
            </div>

            <Separator />

            <div className="flex gap-2">
              <Button onClick={handleSaveAppSettings} disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? t("settings.saving") : t("settings.saveApp")}
              </Button>
              <Button variant="outline" onClick={handleResetAppSettings}>
                <RotateCcw className="mr-2 h-4 w-4" />
                {t("settings.reset")}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* About */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t("settings.about")}</CardTitle>
            <CardDescription>
              {t("home.subtitle")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <p className="text-sm font-medium">{t("settings.version")}</p>
                <p className="text-sm text-muted-foreground">1.0.0</p>
              </div>
              <div>
                <p className="text-sm font-medium">{t("settings.frontend")}</p>
                <p className="text-sm text-muted-foreground">Next.js 16 + React 19</p>
              </div>
              <div>
                <p className="text-sm font-medium">{t("settings.uiLibrary")}</p>
                <p className="text-sm text-muted-foreground">shadcn/ui</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
