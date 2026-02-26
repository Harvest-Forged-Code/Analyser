import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  TrendingDown,
  Target,
  Upload,
  Map,
  Settings,
  Sun,
  Moon,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Wallet,
} from "lucide-react";
import { useNavigationStore } from "@/stores/navigation-store";
import { useThemeStore } from "@/stores/theme-store";
import { useAuthStore } from "@/stores/auth-store";
import { useUpdateStore } from "@/stores/update-store";
import { useAppVersion } from "@/api/hooks/use-settings";
import { useUpdateCheck } from "@/api/hooks/use-update-check";
import { UpdateNotificationDialog } from "@/components/update-notification-dialog";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/earnings", label: "Earnings", icon: TrendingUp },
  { to: "/expenses", label: "Expenses", icon: TrendingDown },
  { to: "/budget-goals", label: "Budget Goals", icon: Target },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/mapper-hub", label: "Mapper Hub", icon: Map },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function AppShell() {
  const { isSidebarCollapsed, toggleSidebar } = useNavigationStore();
  const { theme, toggleTheme } = useThemeStore();
  const { logout } = useAuthStore();
  const { data: version } = useAppVersion();
  const navigate = useNavigate();

  // Auto-update check
  const { data: updateResult } = useUpdateCheck();
  const { skippedVersion, dismissedForSession, skipVersion, dismissForSession } =
    useUpdateStore();

  const showUpdateDialog =
    updateResult?.update_available === true &&
    updateResult.release != null &&
    !dismissedForSession &&
    skippedVersion !== updateResult.latest_version;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300",
          isSidebarCollapsed ? "w-16" : "w-64",
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center border-b border-sidebar-border px-4">
          <Wallet className="h-6 w-6 text-sidebar-primary flex-shrink-0" />
          {!isSidebarCollapsed && (
            <div className="ml-3 flex flex-col min-w-0">
              <span className="text-lg font-semibold text-sidebar-foreground leading-tight">
                Budget Analyser
              </span>
              <span className="text-xs text-sidebar-foreground/50 leading-tight">
                {version ? `v${version}` : ""}
              </span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground",
                )
              }
            >
              <item.icon className="h-5 w-5 flex-shrink-0" />
              {!isSidebarCollapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom actions */}
        <div className="border-t border-sidebar-border p-2 space-y-1">
          <button
            onClick={toggleTheme}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            {theme === "light" ? (
              <Moon className="h-5 w-5 flex-shrink-0" />
            ) : (
              <Sun className="h-5 w-5 flex-shrink-0" />
            )}
            {!isSidebarCollapsed && (
              <span>{theme === "light" ? "Dark Mode" : "Light Mode"}</span>
            )}
          </button>

          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <LogOut className="h-5 w-5 flex-shrink-0" />
            {!isSidebarCollapsed && <span>Logout</span>}
          </button>

          <button
            onClick={toggleSidebar}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            {isSidebarCollapsed ? (
              <ChevronRight className="h-5 w-5 flex-shrink-0" />
            ) : (
              <>
                <ChevronLeft className="h-5 w-5 flex-shrink-0" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6">
          <Outlet />
        </div>
      </main>

      {/* Update notification */}
      {showUpdateDialog && updateResult.release && (
        <UpdateNotificationDialog
          open={showUpdateDialog}
          currentVersion={updateResult.current_version}
          release={updateResult.release}
          onSkip={() => skipVersion(updateResult.latest_version)}
          onDismiss={dismissForSession}
        />
      )}
    </div>
  );
}
