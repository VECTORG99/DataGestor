<script>
  import { onMount } from 'svelte';
  import { supabase } from './lib/supabase';

  let crimes = [];
  let loading = true;
  let error = null;

  // KPIs
  let totalCrimes = 0;
  let topBorough = '';
  let topCategory = '';

  onMount(async () => {
    try {
      // Obtenemos los datos desde Supabase
      const { data, error: err } = await supabase
        .from('london_crime_aggregated')
        .select('*')
        .order('total_incidentes', { ascending: false });

      if (err) throw err;
      crimes = data || [];
      
      if (crimes.length > 0) {
        totalCrimes = crimes.reduce((acc, curr) => acc + curr.total_incidentes, 0);
        
        // Calcular Top Borough
        const boroughMap = {};
        crimes.forEach(c => {
          boroughMap[c.municipio] = (boroughMap[c.municipio] || 0) + c.total_incidentes;
        });
        topBorough = Object.entries(boroughMap).sort((a,b) => b[1] - a[1])[0][0];

        // Calcular Top Categoria
        const catMap = {};
        crimes.forEach(c => {
          catMap[c.categoria_delito] = (catMap[c.categoria_delito] || 0) + c.total_incidentes;
        });
        topCategory = Object.entries(catMap).sort((a,b) => b[1] - a[1])[0][0];
      }

    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

<main class="dashboard">
  <header>
    <h1><span class="gradient-text">London Crime</span> Intelligence</h1>
    <p>DataOps Pipeline Dashboard</p>
  </header>

  {#if loading}
    <div class="loader">
      <div class="spinner"></div>
      <p>Cargando datos en tiempo real desde Supabase...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      <h2>Error de conexión</h2>
      <p>{error}</p>
      <p class="hint">Asegúrate de haber ejecutado el pipeline de Python para poblar la base de datos.</p>
    </div>
  {:else if crimes.length === 0}
    <div class="empty-state">
      <h2>Sin Datos</h2>
      <p>Aún no hay datos en Supabase. Por favor, ejecuta el pipeline de ingesta.</p>
    </div>
  {:else}
    <section class="kpi-grid">
      <div class="kpi-card">
        <h3>Total Incidentes (2016)</h3>
        <p class="value">{totalCrimes.toLocaleString()}</p>
      </div>
      <div class="kpi-card">
        <h3>Distrito más Afectado</h3>
        <p class="value">{topBorough}</p>
      </div>
      <div class="kpi-card">
        <h3>Categoría Principal</h3>
        <p class="value">{topCategory}</p>
      </div>
    </section>

    <section class="data-table-container">
      <h2>Top Incidentes por Distrito y Categoría</h2>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Distrito (Borough)</th>
              <th>Categoría de Delito</th>
              <th>Total Incidentes</th>
            </tr>
          </thead>
          <tbody>
            {#each crimes.slice(0, 50) as crime}
              <tr>
                <td>{crime.municipio}</td>
                <td><span class="badge">{crime.categoria_delito}</span></td>
                <td class="numeric">{crime.total_incidentes.toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  {/if}
</main>

<style>
  :global(:root) {
    --bg-color: #0f172a;
    --card-bg: #1e293b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --border: #334155;
    --gradient: linear-gradient(135deg, #60a5fa, #c084fc);
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background-color: var(--bg-color);
    color: var(--text-main);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }

  .dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  header {
    text-align: center;
    margin-bottom: 3rem;
  }

  h1 {
    font-size: 3rem;
    margin: 0;
    font-weight: 800;
    letter-spacing: -1px;
  }

  .gradient-text {
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  header p {
    color: var(--text-muted);
    font-size: 1.2rem;
    margin-top: 0.5rem;
  }

  /* KPIs */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .kpi-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 1rem;
    padding: 2rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    border-color: var(--accent);
  }

  .kpi-card h3 {
    color: var(--text-muted);
    font-size: 1rem;
    margin: 0 0 1rem 0;
    font-weight: 500;
  }

  .kpi-card .value {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  /* Table */
  .data-table-container h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .table-wrapper {
    background-color: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 1rem;
    overflow: hidden;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
  }

  th {
    background-color: rgba(0,0,0,0.2);
    padding: 1.2rem 1.5rem;
    font-weight: 600;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
  }

  td {
    padding: 1.2rem 1.5rem;
    border-bottom: 1px solid var(--border);
  }

  tr:last-child td {
    border-bottom: none;
  }

  tr:hover td {
    background-color: rgba(255,255,255,0.02);
  }

  .numeric {
    font-family: monospace;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .badge {
    background-color: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  /* States */
  .loader, .error-state, .empty-state {
    text-align: center;
    padding: 5rem 0;
    background-color: var(--card-bg);
    border-radius: 1rem;
    border: 1px dashed var(--border);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1.5rem auto;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .error-state svg {
    color: #ef4444;
    margin-bottom: 1rem;
  }

  .error-state .hint {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin-top: 1rem;
  }
</style>
