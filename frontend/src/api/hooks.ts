import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';
import type { EmailMessage, Task, Tag, PaginatedResponse, IMAPAccount } from '@/types';

// Messages
export const useMessages = (
  tag?: string,
  accountId?: number,
  fromAddr?: string,
  dateFrom?: string,
  dateTo?: string,
  limit: number = 50,
  offset: number = 0
) => {
  return useQuery({
    queryKey: ['messages', tag, accountId, fromAddr, dateFrom, dateTo, limit, offset],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<EmailMessage>>('/messages', {
        params: {
          tag,
          account_id: accountId,
          from_addr: fromAddr,
          date_from: dateFrom,
          date_to: dateTo,
          limit,
          offset,
        },
      });
      return response.data;
    },
  });
};

export const useMessage = (id: number) => {
  return useQuery({
    queryKey: ['message', id],
    queryFn: async () => {
      const response = await apiClient.get<EmailMessage>(`/messages/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

// Tags
export const useTags = () => {
  return useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const response = await apiClient.get<Tag[]>('/tags');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Tasks
export const useTasks = (
  status?: 'open' | 'done' | 'dismissed',
  dueBefore?: string,
  dueAfter?: string,
  limit: number = 50,
  offset: number = 0
) => {
  return useQuery({
    queryKey: ['tasks', status, dueBefore, dueAfter, limit, offset],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<Task>>('/tasks', {
        params: {
          status,
          due_before: dueBefore,
          due_after: dueAfter,
          limit,
          offset,
        },
      });
      return response.data;
    },
  });
};

// Accounts
export const useAccounts = () => {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await apiClient.get<IMAPAccount[]>('/accounts');
      return response.data;
    },
  });
};

export const useUpdateTaskStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: number; status: 'open' | 'done' | 'dismissed' }) => {
      const response = await apiClient.patch<Task>(`/tasks/${id}`, { status });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useAddAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ host, username, password }: { host: string; username: string; password: string }) => {
      const response = await apiClient.post<IMAPAccount>('/accounts', { host, username, password });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
};

export const useUpdateAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, displayName, isActive }: { id: number; displayName?: string; isActive?: boolean }) => {
      const response = await apiClient.patch<IMAPAccount>(`/accounts/${id}`, {
        display_name: displayName,
        is_active: isActive,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
};
