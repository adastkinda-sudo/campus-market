export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }
  const token = localStorage.getItem("campus-market-token") || "";
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

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
  return api("/api/uploads", {
    method: "POST",
    body: JSON.stringify({ dataUrl, purpose }),
  });
}

export function campusCardSrc(url) {
  if (!url) return "";
  const separator = url.includes("?") ? "&" : "?";
  const token = localStorage.getItem("campus-market-token") || "";
  return `${url}${separator}token=${encodeURIComponent(token)}`;
}
