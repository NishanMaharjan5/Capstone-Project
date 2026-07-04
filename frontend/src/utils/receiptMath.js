export function formatMoney(value) {
  const amount = Number(value) || 0
  return `Rs. ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function computeLineTotal(item) {
  const quantity = Number(item.quantity) || 1
  const unitPrice = item.unit_price ?? item.price ?? 0
  const total = item.price ?? quantity * unitPrice
  return Number(total) || 0
}

export function normalizeItemsForSave(items) {
  return (items || []).map((item) => ({
    name: item.name || 'Unknown item',
    quantity: Number(item.quantity) || 1,
    unit_price: Number(item.unit_price ?? item.price ?? 0),
  }))
}
