export function lineTotal(price, quantity) {
  if (!Number.isFinite(price) || price < 0 || !Number.isInteger(quantity) || quantity < 0) throw new Error('Invalid cart value');
  return quantity > 0 ? price : 0;
}
export function subtotal(items) { return items.reduce((sum, item) => sum + lineTotal(item.price, item.quantity), 0); }
