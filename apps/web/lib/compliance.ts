import { fetchWithAuth, getApiBase, getStoredToken } from "./auth";

export async function downloadComplianceAuditJson(): Promise<void> {
  const res = await fetchWithAuth("/api/v1/compliance/export?format=json");
  if (!res.ok) throw new Error("Failed to export compliance audit package");
  
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `finsight-compliance-audit-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export function openComplianceAuditHtmlWindow(): void {
  const token = getStoredToken();
  const apiBase = getApiBase();
  // Open direct authenticated export in new tab for browser printing / PDF generation (§20, §32)
  const printUrl = `${apiBase}/api/v1/compliance/export?format=html`;
  
  // Use fetchWithAuth to get HTML content and open in new blob window to maintain auth headers
  fetchWithAuth("/api/v1/compliance/export?format=html")
    .then((res) => {
      if (!res.ok) throw new Error("Failed to generate compliance report");
      return res.text();
    })
    .then((html) => {
      const blob = new Blob([html], { type: "text/html" });
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
    })
    .catch((err) => {
      alert("Unable to open compliance report: " + err.message);
    });
}
