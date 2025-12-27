const conversionRate = 350;

let gpuData = [];
let currentDisplayed = [];
let currentSortKey = null;
let currentSortOrder = "asc";

function enrichGpuData(data) {
  return data.map((gpu) => {
    const efficiency = Number((gpu.hashrate / gpu.power).toFixed(2));
    const dailyProfitArs = gpu.dailyProfitUsd * conversionRate;
    const roi = Math.round(gpu.priceArs / dailyProfitArs);

    return {
      ...gpu,
      efficiency,
      dailyProfit: Math.round(dailyProfitArs),
      roi,
    };
  });
}

function displayTable(dataArray) {
  const tbody = document.getElementById("gpu-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  dataArray.forEach((gpu) => {
    const row = document.createElement("tr");

    const cells = [
      gpu.name,
      gpu.algo,
      gpu.hashrate,
      gpu.power,
      gpu.efficiency.toFixed(2),
      gpu.priceArs,
      gpu.dailyProfit,
      gpu.roi,
    ];

    cells.forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    });

    tbody.appendChild(row);
  });
}

function compareValues(key, order = "asc") {
  return function (a, b) {
    let valueA = a[key];
    let valueB = b[key];

    const isNumber =
      typeof valueA === "number" && typeof valueB === "number";

    if (!isNumber) {
      valueA = String(valueA).toLowerCase();
      valueB = String(valueB).toLowerCase();
    }

    if (valueA < valueB) return order === "asc" ? -1 : 1;
    if (valueA > valueB) return order === "asc" ? 1 : -1;
    return 0;
  };
}

function applySearchFilter() {
  const searchInput = document.getElementById("searchInput");
  const query = searchInput ? searchInput.value.toLowerCase() : "";

  currentDisplayed = gpuData.filter((gpu) =>
    gpu.name.toLowerCase().includes(query)
  );

  if (currentSortKey) {
    currentDisplayed.sort(compareValues(currentSortKey, currentSortOrder));
  }

  displayTable(currentDisplayed);
}

async function loadGpus() {
  try {
    const response = await fetch("data/gpus.json");
    const data = await response.json();
    gpuData = enrichGpuData(data);
    currentDisplayed = [...gpuData];
    displayTable(currentDisplayed);
  } catch (error) {
    console.error("Error cargando JSON", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", applySearchFilter);
  }

  document.querySelectorAll("#gpuTable th").forEach((th) => {
    th.addEventListener("click", () => {
      const sortKey = th.getAttribute("data-key");
      if (!sortKey) return;

      if (currentSortKey === sortKey) {
        currentSortOrder = currentSortOrder === "asc" ? "desc" : "asc";
      } else {
        currentSortKey = sortKey;
        currentSortOrder = "asc";
      }

      currentDisplayed.sort(compareValues(sortKey, currentSortOrder));
      displayTable(currentDisplayed);
    });
  });

  loadGpus();
});
