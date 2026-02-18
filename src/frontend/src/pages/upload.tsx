import { useUploadStats } from "@/api/hooks/use-upload";
import PageHeader from "@/components/page-header";
import UploadKpiCards from "@/components/upload/kpi-cards";
import UploadForm from "@/components/upload/upload-form";
import UploadStatusGrid from "@/components/upload/upload-status-grid";
import { Skeleton } from "@/components/ui/skeleton";

export default function UploadPage() {
  const { data: stats, isLoading: statsLoading } = useUploadStats();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Statements"
        description="Import and manage bank statement CSV files"
      />

      {statsLoading ? (
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : stats ? (
        <UploadKpiCards stats={stats} />
      ) : null}

      <UploadForm />

      <UploadStatusGrid />
    </div>
  );
}
