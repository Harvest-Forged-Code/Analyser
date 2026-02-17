import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";
import AuthLayout from "@/layouts/auth-layout";
import AppShell from "@/layouts/app-shell";
import LoginPage from "@/pages/login";
import DashboardPage from "@/pages/dashboard";
import YearlySummaryPage from "@/pages/yearly-summary";
import EarningsPage from "@/pages/earnings";
import ExpensesPage from "@/pages/expenses";
import PaymentsPage from "@/pages/payments";
import BudgetGoalsPage from "@/pages/budget-goals";
import SavingsPage from "@/pages/savings";
import NetWorthPage from "@/pages/net-worth";
import RecurringPage from "@/pages/recurring";
import UploadPage from "@/pages/upload";
import MapperHubPage from "@/pages/mapper-hub";
import SettingsPage from "@/pages/settings";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Routes>
      {/* Auth routes */}
      <Route element={<AuthLayout />}>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
          }
        />
      </Route>

      {/* Protected app routes */}
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/yearly-summary" element={<YearlySummaryPage />} />
        <Route path="/earnings" element={<EarningsPage />} />
        <Route path="/expenses" element={<ExpensesPage />} />
        <Route path="/payments" element={<PaymentsPage />} />
        <Route path="/budget-goals" element={<BudgetGoalsPage />} />
        <Route path="/savings" element={<SavingsPage />} />
        <Route path="/net-worth" element={<NetWorthPage />} />
        <Route path="/recurring" element={<RecurringPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/mapper-hub" element={<MapperHubPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
