import { useState, useMemo } from 'react';
import { useMessages, useTags } from '@/api/hooks';
import { useUIStore } from '@/store/uiStore';
import { useNavigate } from 'react-router-dom';
import type { EmailMessage } from '@/types';

export function InboxPage() {
  const navigate = useNavigate();
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);
  const selectedTag = useUIStore((state) => state.selectedTag);
  const selectedAccountId = useUIStore((state) => state.selectedAccountId);
  const setSelectedTag = useUIStore((state) => state.setSelectedTag);
  const setSelectedAccountId = useUIStore((state) => state.setSelectedAccountId);

  const { data: messagesData, isLoading, error } = useMessages(
    selectedTag || undefined,
    selectedAccountId || undefined,
    undefined,
    undefined,
    undefined,
    limit,
    offset
  );
  const { data: tagsData } = useTags();

  const messages = messagesData?.items || [];
  const total = messagesData?.total || 0;
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  const handlePreviousPage = () => {
    setOffset(Math.max(0, offset - limit));
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setOffset(offset + limit);
    }
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="flex h-full">
      {/* Filters Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 p-6 overflow-auto">
        <div className="space-y-6">
          {/* Tags Filter */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-3">Tags</h3>
            <div className="space-y-2">
              <button
                onClick={() => setSelectedTag(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedTag === null ? 'bg-slate-100 text-slate-900 font-medium' : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                All Messages
              </button>
              {tagsData?.map((tag) => (
                <button
                  key={tag.tag}
                  onClick={() => setSelectedTag(tag.tag)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex justify-between ${
                    selectedTag === tag.tag
                      ? 'bg-slate-100 text-slate-900 font-medium'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <span>{tag.tag}</span>
                  <span className="text-xs text-slate-500">{tag.count}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Account Filter */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-3">Accounts</h3>
            <div className="space-y-2">
              <button
                onClick={() => setSelectedAccountId(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedAccountId === null
                    ? 'bg-slate-100 text-slate-900 font-medium'
                    : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                All Accounts
              </button>
            </div>
          </div>

          {/* Clear Filters */}
          {(selectedTag || selectedAccountId) && (
            <button
              onClick={() => {
                setSelectedTag(null);
                setSelectedAccountId(null);
              }}
              className="w-full py-2 px-3 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 p-6">
          <h2 className="text-2xl font-bold text-slate-900">Inbox</h2>
          <p className="text-sm text-slate-500">
            {total} message{total !== 1 ? 's' : ''}
            {selectedTag && ` tagged with "${selectedTag}"`}
          </p>
        </div>

        {/* Messages List */}
        <div className="flex-1 overflow-auto">
          {isLoading ? (
            <div className="p-6 text-center text-slate-500">Loading messages...</div>
          ) : error ? (
            <div className="p-6 text-center text-red-600">Error loading messages</div>
          ) : messages.length === 0 ? (
            <div className="p-6 text-center text-slate-500">No messages found</div>
          ) : (
            <div className="divide-y divide-slate-200">
              {messages.map((message: EmailMessage) => (
                <button
                  key={message.id}
                  onClick={() => navigate(`/messages/${message.id}`)}
                  className="w-full text-left p-4 hover:bg-slate-50 transition-colors focus:outline-none focus:bg-slate-100"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2 mb-1">
                        <p className="font-medium text-slate-900 truncate">{message.subject || '(No subject)'}</p>
                        <span className="text-xs text-slate-500 whitespace-nowrap">{formatDate(message.date)}</span>
                      </div>
                      <p className="text-sm text-slate-600 truncate">{message.from_addr || 'Unknown sender'}</p>
                      {message.tags && message.tags.length > 0 && (
                        <div className="mt-2 flex gap-1">
                          {message.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-block px-2 py-1 text-xs bg-slate-100 text-slate-700 rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-white border-t border-slate-200 p-4 flex items-center justify-between">
            <button
              onClick={handlePreviousPage}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-slate-200 text-slate-900 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-300 transition-colors"
            >
              ← Previous
            </button>
            <span className="text-sm text-slate-600">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-slate-200 text-slate-900 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-300 transition-colors"
            >
              Next →
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
