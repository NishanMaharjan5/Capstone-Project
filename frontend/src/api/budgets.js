import { apiRequest } from './client'

export async function getBudgetOverview() {
  return apiRequest('/api/budgets/')
}

export async function getDecisionSupport() {
  return apiRequest('/api/budgets/suggestions')
}

export async function setBudget(category, monthlyLimit) {
  return apiRequest('/api/budgets/', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category, monthly_limit: monthlyLimit }),
  })
}

export async function clearBudget(category) {
  return apiRequest('/api/budgets/', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category }),
  })
}

export async function getMonthlyBudget() {
  return apiRequest('/api/budgets/monthly')
}

export async function setMonthlyBudget(amount) {
  return apiRequest('/api/budgets/monthly', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount }),
  })
}
