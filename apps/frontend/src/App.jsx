import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";

import { Bar, Pie, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  Filler,
} from "chart.js";

const COLORS = { primary: "#1976d2", secondary: "#388e3c", accent: "#f57c00", danger: "#d32f2f", purple: "#7b1fa2", teal: "#00796b", pink: "#c2185b", deepPurple: "#512da8", orange: "#e64a19" };
const PIE_COLORS = [COLORS.primary, COLORS.secondary, COLORS.accent, COLORS.danger, COLORS.purple, COLORS.teal, COLORS.pink, COLORS.deepPurple, COLORS.orange];
const CHART_DEFAULTS = { maxRotation: 45, maxTicksLimit: 20, tension: 0.3, pointRadius: 2, barMaxWidth: 500 };
const TEXT = {
  loading: "Cargando...", missingEnv: "Faltan variables de entorno", dashboardTitle: "London Crime Dashboard",
  totalCrimes: "Total Crímenes", leadingDistrict: "Distrito Líder", mainCategory: "Categoría Principal",
  filteredRecords: "Registros Filtrados", filters: "Filtros", district: "Distrito", category: "Categoría",
  year: "Año", all: "Todos", allF: "Todas", crimes: "Crímenes", borough: "Borough",
  crimesByDistrict: "Crímenes por Distrito", proportionByCategory: "Proporción por Categoría",
  temporalTrend: "Tendencia Temporal", topSubcategories: "Top 10 Subcategorías",
  crimesByDistrictAndYear: "Crímenes por Distrito y Año",
  detailedData: "Datos Detallados", noFilteredData: "No hay datos con los filtros seleccionados.",
};

ChartJS.register(
  CategoryScale, LinearScale, BarElement, ArcElement,
  PointElement, LineElement, Filler,
  Title, Tooltip, Legend
);

const TABLE_NAME = import.meta.env.VITE_SUPABASE_TABLE_NAME || "london_crime_aggregated";
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl || "", supabaseKey || "");

function groupBy(arr, key) {
  return arr.reduce((acc, row) => {
    acc[row[key]] = (acc[row[key]] || 0) + Number(row.total_crimes);
    return acc;
  }, {});
}

function sortedEntries(obj) {
  return Object.entries(obj).sort((a, b) => b[1] - a[1]);
}

export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterBorough, setFilterBorough] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterYear, setFilterYear] = useState("");
  const [mlMetrics, setMlMetrics] = useState(null);

  useEffect(() => {
    async function fetchRows() {
      setLoading(true);
      if (!supabaseUrl || !supabaseKey) {
        setRows([]);
        setLoading(false);
        return;
      }
      // Supabase caps responses at 1000 rows per request,
      // so we paginate in parallel batches.
      const PAGE_SIZE = 1000;
      const CONCURRENT = 10;

      // First, get total count and first page
      const { data: firstPage, count: totalCount, error: firstErr } = await supabase
        .from(TABLE_NAME)
        .select("*", { count: "exact", head: false })
        .order("borough", { ascending: true })
        .range(0, PAGE_SIZE - 1);
      if (firstErr) { setRows([]); setLoading(false); return; }
      if (!firstPage || firstPage.length < PAGE_SIZE || !totalCount) {
        setRows(firstPage || []);
        setLoading(false);
        return;
      }

      // Build range requests for remaining pages
      const ranges = [];
      for (let from = PAGE_SIZE; from < totalCount; from += PAGE_SIZE) {
        ranges.push({ from, to: Math.min(from + PAGE_SIZE - 1, totalCount - 1) });
      }

      // Fetch remaining pages in parallel batches
      let allRows = [firstPage];
      for (let i = 0; i < ranges.length; i += CONCURRENT) {
        const batch = ranges.slice(i, i + CONCURRENT);
        const results = await Promise.all(
          batch.map(({ from, to }) =>
            supabase
              .from(TABLE_NAME)
              .select("*")
              .order("borough", { ascending: true })
              .range(from, to)
              .then(({ data, error }) => error ? null : data)
          )
        );
        allRows.push(...results.filter(Boolean));
      }
      setRows(allRows.flat());
      setLoading(false);
    }
    fetchRows();
  }, []);

  useEffect(() => {
    fetch("/ml/ml_metrics.json")
      .then((r) => r.json())
      .then(setMlMetrics)
      .catch(() => {});
  }, []);

  if (loading) {
    return (
      <Container sx={{ py: 4 }}>
        <Typography variant="h4">{TEXT.loading}</Typography>
      </Container>
    );
  }

  if (!supabaseUrl || !supabaseKey) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">{TEXT.missingEnv}</Alert>
      </Container>
    );
  }

  const distinctBoroughs = [...new Set(rows.map((r) => r.borough))].sort();
  const distinctCategories = [...new Set(rows.map((r) => r.major_category))].sort();
  const distinctYears = [...new Set(rows.map((r) => r.year))].sort();

  const filtered = rows.filter((r) => {
    if (filterBorough && r.borough !== filterBorough) return false;
    if (filterCategory && r.major_category !== filterCategory) return false;
    if (filterYear && r.year !== filterYear) return false;
    return true;
  });

  const totalCrimes = filtered.reduce((s, r) => s + Number(r.total_crimes), 0);
  const boroughTotals = groupBy(filtered, "borough");
  const topBorough = sortedEntries(boroughTotals)[0];
  const categoryTotals = groupBy(filtered, "major_category");
  const topCategory = sortedEntries(categoryTotals)[0];
  const years = [...new Set(filtered.map((r) => r.year))].sort();
  const yearRange = years.length > 1 ? `${years[0]}-${years[years.length - 1]}` : String(years[0]);

  const boroughChart = sortedEntries(boroughTotals).map(([name, value]) => ({ name, crimenes: value }));
  const pieData = sortedEntries(categoryTotals).map(([name, value]) => ({ name, value }));

  const trendObj = filtered.reduce((acc, row) => {
    const key = `${row.year}-${String(row.month).padStart(2, "0")}`;
    acc[key] = (acc[key] || 0) + Number(row.total_crimes);
    return acc;
  }, {});
  const trendChart = Object.entries(trendObj).sort().map(([date, crimenes]) => ({ date, crimenes }));

  const topMinor = sortedEntries(groupBy(filtered, "minor_category")).slice(0, 10);

  function groupByTwo(arr, key1, key2) {
    return arr.reduce((acc, row) => {
      if (!acc[row[key1]]) acc[row[key1]] = {};
      acc[row[key1]][row[key2]] = (acc[row[key1]][row[key2]] || 0) + Number(row.total_crimes);
      return acc;
    }, {});
  }
  const boroughYear = groupByTwo(filtered, "borough", "year");

  const columns = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <Container maxWidth="xl" sx={{ py: 4, px: { xs: 1, sm: 2, md: 3 } }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom align="center">
        {TEXT.dashboardTitle}
      </Typography>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">{TEXT.totalCrimes}</Typography>
            <Typography variant="h4" fontWeight="bold">{totalCrimes.toLocaleString()}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">{TEXT.leadingDistrict}</Typography>
            <Typography variant="h4" fontWeight="bold">{topBorough ? topBorough[0] : "-"}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">{TEXT.mainCategory}</Typography>
            <Typography variant="h4" fontWeight="bold">{topCategory ? topCategory[0] : "-"}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">{TEXT.filteredRecords}</Typography>
            <Typography variant="h4" fontWeight="bold">{filtered.length.toLocaleString()}</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: 4 }}>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom align="center">
          {TEXT.filters}
        </Typography>
        <Grid container spacing={2} justifyContent="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>{TEXT.district}</InputLabel>
              <Select value={filterBorough} label={TEXT.district} onChange={(e) => setFilterBorough(e.target.value)}>
                <MenuItem value="">{TEXT.all}</MenuItem>
                {distinctBoroughs.map((b) => <MenuItem key={b} value={b}>{b}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>{TEXT.category}</InputLabel>
              <Select value={filterCategory} label={TEXT.category} onChange={(e) => setFilterCategory(e.target.value)}>
                <MenuItem value="">{TEXT.allF}</MenuItem>
                {distinctCategories.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>{TEXT.year}</InputLabel>
              <Select value={filterYear} label={TEXT.year} onChange={(e) => setFilterYear(e.target.value)}>
                <MenuItem value="">{TEXT.all}</MenuItem>
                {distinctYears.map((y) => <MenuItem key={y} value={y}>{y}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>{TEXT.crimesByDistrict}</Typography>
        <Bar
          data={{
            labels: boroughChart.map((r) => r.name),
            datasets: [{
              label: TEXT.crimes,
              data: boroughChart.map((r) => r.crimenes),
              backgroundColor: COLORS.primary,
            }],
          }}
          options={{
            responsive: true,
            indexAxis: "x",
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { maxRotation: CHART_DEFAULTS.maxRotation } } },
          }}
        />
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>{TEXT.proportionByCategory}</Typography>
        <Box sx={{ maxWidth: CHART_DEFAULTS.barMaxWidth, mx: "auto" }}>
          <Pie
            data={{
              labels: pieData.map((r) => r.name),
              datasets: [{
                data: pieData.map((r) => r.value),
                backgroundColor: PIE_COLORS,
              }],
            }}
            options={{ responsive: true, plugins: { legend: { position: "bottom" } } }}
          />
        </Box>
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>{TEXT.temporalTrend}</Typography>
        <Line
          data={{
            labels: trendChart.map((r) => r.date),
            datasets: [{
              label: TEXT.crimes,
              data: trendChart.map((r) => r.crimenes),
              borderColor: COLORS.danger,
              backgroundColor: "rgba(211,47,47,0.1)",
              fill: true,
              tension: CHART_DEFAULTS.tension,
              pointRadius: CHART_DEFAULTS.pointRadius,
            }],
          }}
          options={{
            responsive: true,
            scales: { x: { ticks: { maxRotation: CHART_DEFAULTS.maxRotation, maxTicksLimit: CHART_DEFAULTS.maxTicksLimit } } },
          }}
        />
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>{TEXT.topSubcategories}</Typography>
        <Bar
          data={{
            labels: topMinor.map((r) => r[0]),
            datasets: [{
              label: TEXT.crimes,
              data: topMinor.map((r) => r[1]),
              backgroundColor: COLORS.secondary,
            }],
          }}
          options={{
            responsive: true,
            indexAxis: "y",
            plugins: { legend: { display: false } },
          }}
        />
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>{TEXT.crimesByDistrictAndYear}</Typography>
        <Box sx={{ overflowX: "auto" }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold" }}>{TEXT.borough}</TableCell>
                {years.map((y) => (
                  <TableCell key={y} sx={{ fontWeight: "bold" }} align="right">{y}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(boroughYear).map(([borough, yearsData]) => (
                <TableRow key={borough}>
                  <TableCell>{borough}</TableCell>
                  {years.map((y) => (
                    <TableCell key={y} align="right">
                      {yearsData[y]?.toLocaleString() || "0"}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      </Paper>

      <Typography variant="h6" gutterBottom>{TEXT.detailedData}</Typography>
      {filtered.length === 0 ? (
        <Alert severity="info">{TEXT.noFilteredData}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                {columns.map((col) => (
                  <TableCell key={col} sx={{ fontWeight: "bold" }}>{col}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.slice(0, 100).map((row, idx) => (
                <TableRow key={idx}>
                  {columns.map((col) => (
                    <TableCell key={col}>{row[col] != null ? String(row[col]) : "-"}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* ML Insights Section */}
      <Box sx={{ mt: 6, mb: 2 }}>
        <Typography variant="h5" fontWeight="bold" gutterBottom align="center">
          ML Insights — Clasificación de Criminalidad
        </Typography>
        {mlMetrics && (
          <>
            <Typography variant="subtitle2" align="center" color="text.secondary" gutterBottom>
              Modelo: {mlMetrics.model} — Predice si un crimen es "alto" (&gt;mediana) o "bajo"
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              {[
                { label: "Accuracy", value: (mlMetrics.accuracy * 100).toFixed(1) + "%", color: COLORS.secondary },
                { label: "Precision", value: (mlMetrics.precision * 100).toFixed(1) + "%", color: COLORS.primary },
                { label: "Recall", value: (mlMetrics.recall * 100).toFixed(1) + "%", color: COLORS.accent },
                { label: "F1 Score", value: (mlMetrics.f1_score * 100).toFixed(1) + "%", color: COLORS.purple },
                { label: "ROC AUC", value: mlMetrics.roc_auc.toFixed(4), color: COLORS.teal },
                { label: "Gini", value: mlMetrics.gini.toFixed(4), color: COLORS.pink },
              ].map((m) => (
                <Grid item xs={6} sm={4} md={2} key={m.label}>
                  <Card>
                    <CardContent sx={{ textAlign: "center", py: 1.5 }}>
                      <Typography variant="body2" color="text.secondary">{m.label}</Typography>
                      <Typography variant="h5" fontWeight="bold" sx={{ color: m.color }}>{m.value}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 1.5, textAlign: "center" }}>
                  <Typography variant="subtitle2" gutterBottom>Matriz de Confusión</Typography>
                  <Box sx={{ display: "flex", justifyContent: "center" }}>
                    <Box sx={{ display: "inline-grid", gridTemplateColumns: "auto 1fr 1fr", gap: 1, alignItems: "center" }}>
                      <Box /><Typography variant="caption" sx={{ fontWeight: "bold", textAlign: "center" }}>Pred. Bajo</Typography><Typography variant="caption" sx={{ fontWeight: "bold", textAlign: "center" }}>Pred. Alto</Typography>
                      <Typography variant="caption" sx={{ fontWeight: "bold" }}>Real Bajo</Typography>
                      <Box sx={{ bgcolor: "#e8f5e9", border: 1, borderColor: "success.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.true_negatives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">VN</Typography></Box>
                      <Box sx={{ bgcolor: "#ffebee", border: 1, borderColor: "error.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.false_positives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">FP</Typography></Box>
                      <Typography variant="caption" sx={{ fontWeight: "bold" }}>Real Alto</Typography>
                      <Box sx={{ bgcolor: "#ffebee", border: 1, borderColor: "error.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.false_negatives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">FN</Typography></Box>
                      <Box sx={{ bgcolor: "#e8f5e9", border: 1, borderColor: "success.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.true_positives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">VP</Typography></Box>
                    </Box>
                  </Box>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 1.5, textAlign: "center" }}>
                  <Typography variant="subtitle2" gutterBottom>Curva ROC</Typography>
                  <Box sx={{ position: "relative", width: "100%", maxWidth: 400, mx: "auto" }}>
                    <svg viewBox="0 0 100 100" style={{ width: "100%", height: "auto" }}>
                      {/* diagonal reference */}
                      <line x1="0" y1="100" x2="100" y2="0" stroke="#ccc" strokeWidth="0.5" strokeDasharray="3,3" />
                      {/* ROC curve */}
                      <polyline
                        fill="none"
                        stroke={COLORS.primary}
                        strokeWidth="1.5"
                        points={mlMetrics.roc_curve.fpr.map((f, i) => {
                          const x = f * 100;
                          const y = 100 - mlMetrics.roc_curve.tpr[i] * 100;
                          return `${x},${y}`;
                        }).join(" ")}
                      />
                      {/* axis labels */}
                      <text x="50" y="97" fontSize="3" textAnchor="middle" fill="#666">Tasa de Falsos Positivos (FPR)</text>
                      <text x="-50" y="2" fontSize="3" textAnchor="middle" fill="#666" transform="rotate(-90, -50, 2)">Tasa de Verdaderos Positivos (TPR)</text>
                    </svg>
                    <Typography variant="caption" display="block" color="text.secondary">
                      AUC = {mlMetrics.roc_auc.toFixed(4)}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </>
        )}
        {!mlMetrics && (
          <Alert severity="info">Ejecuta el pipeline de ML para ver métricas de clasificación.</Alert>
        )}
      </Box>
    </Container>
  );
}
