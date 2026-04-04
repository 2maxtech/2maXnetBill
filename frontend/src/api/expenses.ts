import client from './client';

export interface ExpenseType {
  id: string;
  category: string;
  description: string;
  amount: string;
  date: string;
  receipt_number: string | null;
  recorded_by: string | null;
  created_at: string;
}

export const getExpenses = (params?: any) =>
  client.get<{ items: ExpenseType[]; total: number }>('/expenses/', { params });
export const createExpense = (data: any) => client.post<ExpenseType>('/expenses/', data);
export const updateExpense = (id: string, data: any) => client.put<ExpenseType>(`/expenses/${id}`, data);
export const deleteExpense = (id: string) => client.delete(`/expenses/${id}`);
export const getExpenseSummary = (params?: any) => client.get('/expenses/summary', { params });
