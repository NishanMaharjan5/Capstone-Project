import { apiRequest } from './client'

export async function getIncome() {
  return apiRequest('/api/income/')
}

export async function addIncome({ amount, source, date }) {
  return apiRequest('/api/income/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, source, date }),
  })
}

export async function deleteIncome(id) {
  return apiRequest(`/api/income/${id}`, {
    method: 'DELETE',
  })
}
