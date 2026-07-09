export function money(value) {
  const number = Number(value || 0);
  return `¥${Number.isInteger(number) ? number : number.toFixed(2)}`;
}

export function truncateText(text, length = 60) {
  const value = String(text || "");
  return value.length > length ? `${value.slice(0, length)}...` : value;
}

export function shortTime(value) {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
}

export function discountPercent(item) {
  const original = Number(item.originalPrice || 0);
  const sell = Number(item.sellPrice || 0);
  if (!original || sell >= original) return "";
  return `省 ${Math.round((1 - sell / original) * 100)}%`;
}

export function defaultImage(item) {
  return item?.imageUrl || "/assets/kettle.svg";
}
