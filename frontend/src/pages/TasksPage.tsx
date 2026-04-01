import { useState } from 'react';
import { useTasks, useUpdateTaskStatus } from '@/api/hooks';
import { useUIStore } from '@/store/uiStore';
import type { Task } from '@/types';

export function TasksPage() {
  const [status, setStatus] = useState<'open' | 'done' | 'dismissed' | null>(null);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const { data: tasksData, isLoading, error, refetch } = useTasks(
    status || undefined,
    undefined,
    undefined,
    limit,
    offset
  );

  const updateTaskStatusMutation = useUpdateTaskStatus();

  const tasks = tasksData?.items || [];
  const total = tasksData?.total || 0;
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const handleStatusChange = (taskId: number, currentStatus: string) => {
    let newStatus: 'open' | 'done' | 'dismissed';
    if (currentStatus === 'open') newStatus = 'done';
    else if (currentStatus === 'done') newStatus = 'dismissed';
    else newStatus = 'open';

    updateTaskStatusMutation.mutate({ taskId, status: newStatus }, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'No due date';
    const date = new Date(dateString);
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === now.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    if (date < now) return `Overdue: ${date.toLocaleDateString()}`;
    return date.toLocaleDateString();
  };

  const getStatusColor = (taskStatus: string) => {
    switch (taskStatus) {
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'done':
        return 'bg-green-100 text-green-800';
      case 'dismissed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-slate-100 text-slate-800';
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">Tasks</h1>

      {/* Filters */}
      <div className="flex gap-4 mb-8">
        <select
          value={status || ''}
          onChange={(e) => {
            setStatus((e.target.value as any) || null);
            setOffset(0);
          }}
          className="px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="done">Done</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>

      {/* Task List */}
      <div className="space-y-4">
        {isLoading && <p className="text-slate-600">Loading tasks...</p>}
        {error && <p className="text-red-600">Error loading tasks: {error.message}</p>}
        {!isLoading && tasks.length === 0 && <p className="text-slate-600">No tasks found.</p>}

        {tasks.map((task: Task) => (
          <div key={task.id} className="bg-white border border-slate-200 rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{task.title}</h3>
                <div className="flex gap-4 text-sm text-slate-600">
                  <span>Due: {formatDate(task.due_date)}</span>
                  <span>Confidence: {(task.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="flex gap-2 items-center">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(task.status)}`}>
                  {task.status}
                </span>
                <button
                  onClick={() => handleStatusChange(task.id, task.status)}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
                  disabled={updateTaskStatusMutation.isPending}
                >
                  {task.status === 'open' ? 'Complete' : task.status === 'done' ? 'Dismiss' : 'Reopen'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex justify-between items-center">
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={currentPage === 1}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-200 text-slate-900 hover:bg-slate-300 disabled:opacity-50 transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-slate-600">
            Page {currentPage} of {totalPages} ({total} tasks)
          </span>
          <button
            onClick={() => setOffset(offset + limit)}
            disabled={currentPage >= totalPages}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-slate-200 text-slate-900 hover:bg-slate-300 disabled:opacity-50 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
