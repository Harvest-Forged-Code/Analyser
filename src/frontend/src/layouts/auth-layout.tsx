import { Outlet } from "react-router-dom";

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 via-background to-primary/5">
      <div className="flex min-h-screen items-center justify-center p-4">
        <Outlet />
      </div>
    </div>
  );
}
