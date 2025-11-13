/**
 * Fuente de datos inicial.
 * Ahora se obtiene desde data/gpus.json para emular
 * el flujo que luego manejará un backend/API real.
 */
let gpus = [];
let lastDataSource = "";

const USD_ARS = 1000; // TODO: traer de API o actualizar manual
const ENERGY_ARS_PER_KWH = 80; // TODO: ajustar al costo real AR

function gpuMetrics(gpu) {
  const efficiency = gpu.hashrate / gpu.power; // MH/s por W
  const dailyRevenueArs = gpu.dailyProfitUsd * USD_ARS;

  // Consumo diario kWh = (W / 1000) * 24
  const dailyEnergyKwh = (gpu.power / 1000) * 24;
  const dailyEnergyCostArs = dailyEnergyKwh * ENERGY_ARS_PER_KWH;
  const dailyNetArs = dailyRevenueArs - dailyEnergyCostArs;

  // ROI en días (si dailyNetArs <= 0 -> infinito)
  const roiDays = dailyNetArs > 0 ? gpu.priceArs / dailyNetArs : Infinity;

  // "Best value score" simple: neto diario * eficiencia
  const score = dailyNetArs * efficiency;

  return {
    efficiency,
    dailyRevenueArs,
    dailyEnergyCostArs,
    dailyNetArs,
    roiDays,
    score,
  };
}

function formatCurrency(ars) {
  return ars.toLocaleString("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  });
}

function formatNumber(n, digits = 2) {
  if (!isFinite(n)) return "—";
  return n.toLocaleString("es-AR", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function buildTable(filtered) {
  const container = document.getElementById("tableContainer");
  if (!container) return;

  if (!filtered.length) {
    container.innerHTML = `
      <div class="empty-state">
        No hay GPUs cargadas aún.
      </div>
    `;
    return;
  }

  const rows = filtered
    .map((gpu, index) => {
      const m = gpuMetrics(gpu);
      const isBest = index === 0;
      const highPower = gpu.power > 200;

      return `
        <tr>
          <td>${index + 1}</td>
          <td>
            <div>${gpu.name}</div>
            <div style="font-size:0.75rem;color:#9ca3af;">
              ${gpu.algo.toUpperCase()}
            </div>
          </td>
          <td>${gpu.hashrate} MH/s</td>
          <td>${gpu.power} W ${
            highPower
              ? '<span class="badge badge-warn">Alto consumo</span>'
              : ""
          }</td>
          <td>${formatCurrency(gpu.priceArs)}</td>
          <td>${formatNumber(m.efficiency, 2)}</td>
          <td>${formatCurrency(m.dailyNetArs)}</td>
          <td>${
            isBest
              ? `<span class="badge badge-best">Mejor valor</span>`
              : formatNumber(m.roiDays, 0) + " días"
          }</td>
        </tr>
      `;
    })
    .join("");

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>GPU</th>
          <th>Hashrate</th>
          <th>Power</th>
          <th>Precio ARS</th>
          <th>MH/s · W⁻¹</th>
          <th>Neto diario (ARS)</th>
          <th>ROI estimado</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  `;
}

function applyFilters() {
  const search = document.getElementById("searchInput")?.value
    .toLowerCase()
    .trim();
  const algo = document.getElementById("algoSelect")?.value;
  const sort = document.getElementById("sortSelect")?.value;

  let result = [...gpus];

  if (search) {
    result = result.filter((gpu) =>
      gpu.name.toLowerCase().includes(search)
    );
  }

  if (algo) {
    result = result.filter((gpu) => gpu.algo === algo);
  }

  result.sort((a, b) => {
    const ma = gpuMetrics(a);
    const mb = gpuMetrics(b);

    switch (sort) {
      case "hashrate":
        return mb.hashrate - ma.hashrate;
      case "efficiency":
        return mb.efficiency - ma.efficiency;
      case "price":
        return ma.priceArs - mb.priceArs;
      case "roi":
        return ma.roiDays - mb.roiDays;
      case "bestValue":
      default:
        return mb.score - ma.score;
    }
  });

  buildTable(result);
}

function resolveApiCandidates() {
  const params = new URLSearchParams(window.location.search);
  const explicit = params.get("api") || window.BESTVALUEGPU_API_BASE;
  const candidates = [];

  if (explicit) {
    const normalized = explicit.replace(/\/$/, "");
    candidates.push(`${normalized}/gpus`);
  }

  candidates.push("/api/gpus");
  candidates.push("data/gpus.json");

  return [...new Set(candidates)];
}

async function fetchGpusFromSources() {
  const errors = [];
  for (const endpoint of resolveApiCandidates()) {
    try {
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      if (!Array.isArray(data)) {
        throw new Error("Formato de datos inválido");
      }
      lastDataSource = endpoint;
      return data;
    } catch (error) {
      errors.push(`${endpoint}: ${error.message}`);
    }
  }

  throw new Error(errors.join("\n"));
}

async function loadGpus() {
  const container = document.getElementById("tableContainer");
  if (container) {
    container.innerHTML = `
      <div class="empty-state">
        Cargando datos de GPUs...
      </div>
    `;
  }

  try {
    gpus = await fetchGpusFromSources();
    applyFilters();
  } catch (error) {
    console.error(error);
    if (container) {
      container.innerHTML = `
        <div class="empty-state">
          Error al cargar los datos.
          <br />
          <small>${error.message.replace(/\n/g, "<br />")}</small>
        </div>
      `;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  ["searchInput", "algoSelect", "sortSelect"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", applyFilters);
    if (el && el.tagName === "SELECT") el.addEventListener("change", applyFilters);
  });

  loadGpus();
});
