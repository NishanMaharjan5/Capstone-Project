import { apiRequest } from './client'

export async function getReceipts() {
  return apiRequest('/api/receipts/')
}

export async function uploadReceipt(imageFile) {
  const formData = new FormData()
  formData.append('image', imageFile)

  return apiRequest('/api/receipts/upload', {
    method: 'POST',
    body: formData,
  })
}

export async function saveReceipt(payload) {
  return apiRequest('/api/receipts/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function addManualReceipt(payload) {
  return apiRequest('/api/receipts/manual', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteReceipt(id) {
  return apiRequest(`/api/receipts/${id}`, {
    method: 'DELETE',
  })
}
