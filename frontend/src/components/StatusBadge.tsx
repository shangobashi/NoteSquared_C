interface StatusBadgeProps {
  status: string;
}

const statusConfig: Record<string, { label: string; color: string }> = {
  CREATED: { label: 'Created', color: 'bg-gray-600' },
  UPLOADED: { label: 'Uploaded', color: 'bg-blue-600' },
  TRANSCRIBING: { label: 'Transcribing...', color: 'bg-yellow-600' },
  EXTRACTING: { label: 'Analyzing...', color: 'bg-yellow-600' },
  GENERATING: { label: 'Generating...', color: 'bg-yellow-600' },
  COMPLETED: { label: 'Completed', color: 'bg-emerald-600' },
  FAILED: { label: 'Failed', color: 'bg-red-600' },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, color: 'bg-gray-600' };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${config.color}`}
    >
      {config.label}
    </span>
  );
}
