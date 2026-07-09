import { api } from "../client.js";

export function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export async function uploadImage(file, purpose) {
  const dataUrl = await fileToDataUrl(file);
  return api("/api/uploads", { method: "POST", body: JSON.stringify({ dataUrl, purpose }) });
}

export function campusCardSrc(url) {
  if (!url) return "";
  const separator = url.includes("?") ? "&" : "?";
  const token = localStorage.getItem("campus-market-token") || "";
  return `${url}${separator}token=${encodeURIComponent(token)}`;
}
