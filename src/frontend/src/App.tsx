import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";
import AuthLayout from "@/layouts/auth-layout";
import AppShell from "@/layouts/app-shell";
import LoginPage from "@/pages/login";
import DashboardPage from "@/pages/dashboard";
import EarningsPage from "@/pages/earnings";
import ExpensesPage from "@/pages/expenses";
import BudgetGoalsPage from "@/pages/budget-goals";
import UploadPage from "@/pages/upload";
import MapperHubPage from "@/pages/mapper-hub";
import SettingsPage from "@/pages/settings";
import PaymentsPage from "@/pages/payments";

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
        <Route path="/earnings" element={<EarningsPage />} />
        <Route path="/expenses" element={<ExpensesPage />} />
        <Route path="/budget-goals" element={<BudgetGoalsPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/mapper-hub" element={<MapperHubPage />} />
        <Route path="/payments" element={<PaymentsPage />} />
        <Route path="/recurring" element={<Navigate to="/payments" replace />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
