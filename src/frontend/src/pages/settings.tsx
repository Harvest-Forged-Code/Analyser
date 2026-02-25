import { Settings, Lock, FileText } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import PageHeader from "@/components/page-header";
import { useThemeStore } from "@/stores/theme-store";
import LoggingTab from "@/components/settings/logging-tab";
import SecurityTab from "@/components/settings/security-tab";
import ConfigurationTab from "@/components/settings/configuration-tab";

const tabs = [
  { value: "logging", label: "Logging", icon: Settings },
  { value: "security", label: "Security", icon: Lock },
  { value: "configuration", label: "Configuration", icon: FileText },
] as const;

export default function SettingsPage() {
  const { theme } = useThemeStore();
  const isDark = theme === "dark";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Configure application preferences"
      />

      <Tabs defaultValue="logging" className="space-y-6">
        <TabsList>
          {tabs.map(({ value, label, icon: Icon }) => (
            <TabsTrigger key={value} value={value} className="gap-2">
              <Icon className="h-4 w-4" />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="logging">
          <LoggingTab />
        </TabsContent>

        <TabsContent value="security">
          <SecurityTab />
        </TabsContent>

        <TabsContent value="configuration">
          <ConfigurationTab isDark={isDark} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
