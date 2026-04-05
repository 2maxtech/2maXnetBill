import api from './client'

export interface ExpenseType {
  id: string
  category: string
  description: string
  amount: number | string
  date: string
  receipt_number: string | null
  recorded_by: string | null
  created_at: string
}

export interface ExpenseSummary {
  category: string
  total: number
}

export function getExpenses(params?: { page?: number; page_size?: number; category?: string; date_from?: string; date_to?: string }) {
  return api.get<{ items: ExpenseType[]; total: number }>('/expenses/', { params })
}

export function createExpense(data: Partial<ExpenseType>) {
  return api.post<ExpenseType>('/expenses/', data)
}

export function updateExpense(id: string, data: Partial<ExpenseType>) {
  return api.put<ExpenseType>(`/expenses/${id}`, data)
}

export function deleteExpense(id: string) {
  return api.delete(`/expenses/${id}`)
}

export function getExpenseSummary(params?: { date_from?: string; date_to?: string }) {
  return api.get<ExpenseSummary[]>('/expenses/summary', { params })
}
