import PageHeader from "@/components/page-header";
import UploadForm from "@/components/upload/upload-form";

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Statements"
        description="Import and manage bank statement CSV files"
      />

      <UploadForm />
    </div>
  );
}
