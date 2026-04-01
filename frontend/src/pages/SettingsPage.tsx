import { useState } from 'react';
import { useAccounts, useCreateAccount, useUpdateAccount, useAuthTokens, useCreateAuthToken, useRevokeAuthToken } from '@/api/hooks';
import { useUIStore } from '@/store/uiStore';

export function SettingsPage() {
  const apiToken = useUIStore((state) => state.apiToken);
  const [showAddAccountModal, setShowAddAccountModal] = useState(false);
  const [showCreateTokenModal, setShowCreateTokenModal] = useState(false);
  const [accountForm, setAccountForm] = useState({ host: '', username: '', password: '' });
  const [tokenForm, setTokenForm] = useState({ ttl_minutes: 24 * 60, note: '' });
  const [newTokenDisplay, setNewTokenDisplay] = useState<string | null>(null);

  const { data: accounts, isLoading: accountsLoading } = useAccounts();
  const { data: tokens, isLoading: tokensLoading } = useAuthTokens();
  const createAccountMutation = useCreateAccount();
  const updateAccountMutation = useUpdateAccount();
  const createTokenMutation = useCreateAuthToken();
  const revokeTokenMutation = useRevokeAuthToken();

    const isAdmin = !tokensError;

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountForm.host || !accountForm.username || !accountForm.password) return;
    createAccountMutation.mutate(accountForm, {
      onSuccess: () => {
        setAccountForm({ host: '', username: '', password: '' });
        setShowAddAccountModal(false);
      },
    });
  };

  const handleToggleActive = (accountId: number, isActive: boolean) => {
    updateAccountMutation.mutate({
      id: accountId,
      updates: { is_active: !isActive },
    });
  };

  const handleCreateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    createTokenMutation.mutate(
      { ttl_minutes: tokenForm.ttl_minutes, note: tokenForm.note },
      {
        onSuccess: (token) => {
          setNewTokenDisplay(token.token);
          setTokenForm({ ttl_minutes: 24 * 60, note: '' });
        },
      }
    );
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">Settings</h1>

      {/* Accounts Section */}
      <section className="mb-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-slate-900">IMAP Accounts</h2>
          <button
            onClick={() => setShowAddAccountModal(true)}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Add Account
          </button>
        </div>

        {accountsLoading && <p className="text-slate-600">Loading accounts...</p>}
        {accounts && accounts.length === 0 && <p className="text-slate-600">No accounts configured.</p>}

        <div className="space-y-4">
          {accounts?.map((account) => (
            <div
              key={account.id}
              className="bg-white border border-slate-200 rounded-lg p-6 flex justify-between items-center"
            >
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-slate-900">
                  {account.display_name || account.username}
                </h3>
                <p className="text-sm text-slate-600">
                  {account.host} • {account.username}
                </p>
                <p className="text-xs text-slate-500 mt-1">Last UID: {account.last_uid}</p>
              </div>
              <div className="flex gap-4 items-center">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={account.is_active || false}
                    onChange={() => handleToggleActive(account.id, account.is_active || false)}
                    className="w-4 h-4 rounded border-slate-300"
                  />
                  Active
                </label>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Admin Token Section */}
      {isAdmin && (
        <section className="mb-12">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-slate-900">API Tokens (Admin)</h2>
            <button
              onClick={() => setShowCreateTokenModal(true)}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
            >
              Create Token
            </button>
          </div>

          {tokensLoading && <p className="text-slate-600">Loading tokens...</p>}
          {tokens && tokens.length === 0 && <p className="text-slate-600">No tokens created.</p>}

          <div className="space-y-4">
            {tokens?.map((token) => (
              <div
                key={token.token}
                className="bg-white border border-slate-200 rounded-lg p-6 flex justify-between items-center"
              >
                <div className="flex-1">
                  <p className="text-sm font-mono text-slate-700">Token: ...{token.hint}</p>
                  <p className="text-xs text-slate-600 mt-1">Source: {token.source}</p>
                  <p className="text-xs text-slate-600">
                    Created: {new Date(token.created_at).toLocaleString()}
                  </p>
                  {token.expires_at && (
                    <p className="text-xs text-slate-600">
                      Expires: {new Date(token.expires_at).toLocaleString()}
                    </p>
                  )}
                  {token.note && <p className="text-xs text-slate-600 mt-1">Note: {token.note}</p>}
                </div>
                <button
                  onClick={() => revokeTokenMutation.mutate(token.token)}
                  disabled={token.is_revoked || revokeTokenMutation.isPending}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 transition-colors"
                >
                  {token.is_revoked ? 'Revoked' : 'Revoke'}
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Add Account Modal */}
      {showAddAccountModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-slate-900 mb-4">Add IMAP Account</h3>
            <form onSubmit={handleAddAccount} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Host</label>
                <input
                  type="text"
                  placeholder="imap.gmail.com"
                  value={accountForm.host}
                  onChange={(e) => setAccountForm({ ...accountForm, host: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
                <input
                  type="email"
                  placeholder="your@email.com"
                  value={accountForm.username}
                  onChange={(e) => setAccountForm({ ...accountForm, username: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={accountForm.password}
                  onChange={(e) => setAccountForm({ ...accountForm, password: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  disabled={createAccountMutation.isPending}
                  className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {createAccountMutation.isPending ? 'Adding...' : 'Add'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddAccountModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-slate-200 text-slate-900 hover:bg-slate-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Token Modal */}
      {showCreateTokenModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-semibold text-slate-900 mb-4">Create API Token</h3>
            {newTokenDisplay ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-700 font-medium">Your new token (save this, it won't be shown again):</p>
                <div className="bg-slate-100 p-4 rounded-lg break-all font-mono text-xs text-slate-900">
                  {newTokenDisplay}
                </div>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(newTokenDisplay);
                    setNewTokenDisplay(null);
                    setShowCreateTokenModal(false);
                  }}
                  className="w-full px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  Copy & Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreateToken} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">TTL (minutes)</label>
                  <input
                    type="number"
                    min="0"
                    value={tokenForm.ttl_minutes}
                    onChange={(e) => setTokenForm({ ...tokenForm, ttl_minutes: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Note (optional)</label>
                  <input
                    type="text"
                    placeholder="e.g., CI/CD deployment"
                    value={tokenForm.note}
                    onChange={(e) => setTokenForm({ ...tokenForm, note: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
                <div className="flex gap-4 pt-4">
                  <button
                    type="submit"
                    disabled={createTokenMutation.isPending}
                    className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                  >
                    {createTokenMutation.isPending ? 'Creating...' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateTokenModal(false)}
                    className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-slate-200 text-slate-900 hover:bg-slate-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
