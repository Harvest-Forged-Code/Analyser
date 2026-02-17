import { useState, useMemo } from "react";
import { Settings, Lock, AlertCircle, CheckCircle } from "lucide-react";
import {
  useLogLevels,
  useCurrentLogLevel,
  useSetLogLevel,
  useChangePassword,
} from "@/api/hooks/use-settings";
import PageHeader from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function SettingsPage() {
  const { data: logLevels, isLoading: levelsLoading } = useLogLevels();
  const { data: currentLevel, isLoading: currentLoading } = useCurrentLogLevel();
  const setLogLevelMutation = useSetLogLevel();

  const [selectedLogLevel, setSelectedLogLevel] = useState<string>("");
  const [currentPassword, setCurrentPassword] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [passwordMessage, setPasswordMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const changePasswordMutation = useChangePassword();

  // Set initial log level
  useMemo(() => {
    if (currentLevel && !selectedLogLevel) {
      setSelectedLogLevel(currentLevel.log_level);
    }
  }, [currentLevel, selectedLogLevel]);

  const handleSaveLogLevel = async () => {
    if (!selectedLogLevel) return;
    try {
      await setLogLevelMutation.mutateAsync(selectedLogLevel);
      alert("Log level updated successfully!");
    } catch (error) {
      alert(`Failed to update log level: ${error}`);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordMessage({ type: "error", text: "All fields are required" });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: "error", text: "New password and confirmation do not match" });
      return;
    }

    if (newPassword.length < 6) {
      setPasswordMessage({ type: "error", text: "Password must be at least 6 characters" });
      return;
    }

    try {
      await changePasswordMutation.mutateAsync({
        current: currentPassword,
        new_password: newPassword,
        confirm: confirmPassword,
      });
      setPasswordMessage({ type: "success", text: "Password changed successfully!" });
      // Clear form
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      setPasswordMessage({ type: "error", text: `Failed to change password: ${error}` });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Configure application preferences"
      />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              <CardTitle>Logging</CardTitle>
            </div>
            <CardDescription>
              Configure application logging level
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {levelsLoading || currentLoading ? (
              <Skeleton className="h-32 w-full" />
            ) : (
              <>
                <div className="space-y-2">
                  <Label>Current Log Level</Label>
                  <div>
                    <Badge variant="default">
                      {currentLevel?.log_level || "Not set"}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="log-level">Select Log Level</Label>
                  <Select value={selectedLogLevel} onValueChange={setSelectedLogLevel}>
                    <SelectTrigger id="log-level">
                      <SelectValue placeholder="Select log level" />
                    </SelectTrigger>
                    <SelectContent>
                      {logLevels && logLevels.length > 0 ? (
                        logLevels.map((level) => (
                          <SelectItem key={level} value={level}>
                            {level}
                          </SelectItem>
                        ))
                      ) : (
                        <SelectItem value="none" disabled>
                          No levels available
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={handleSaveLogLevel}
                  disabled={!selectedLogLevel || setLogLevelMutation.isPending}
                  className="w-full"
                >
                  {setLogLevelMutation.isPending ? "Saving..." : "Save Log Level"}
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              <CardTitle>Security</CardTitle>
            </div>
            <CardDescription>
              Change your application password
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current-password">Current Password</Label>
                <Input
                  id="current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">New Password</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm New Password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                />
              </div>

              {passwordMessage && (
                <div
                  className={`flex items-center gap-2 p-3 rounded-lg ${
                    passwordMessage.type === "success"
                      ? "bg-green-50 text-green-700 border border-green-200"
                      : "bg-red-50 text-red-700 border border-red-200"
                  }`}
                >
                  {passwordMessage.type === "success" ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <span className="text-sm">{passwordMessage.text}</span>
                </div>
              )}

              <Button
                type="submit"
                disabled={changePasswordMutation.isPending}
                className="w-full"
              >
                {changePasswordMutation.isPending ? "Changing..." : "Change Password"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
