import { useEffect, useMemo, useState } from "react";
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
import TablePagination from "@mui/material/TablePagination";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Chip from "@mui/material/Chip";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Drawer from "@mui/material/Drawer";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import Divider from "@mui/material/Divider";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import TimelineIcon from "@mui/icons-material/Timeline";

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
const SURFACE_COLORS = {
  raw: "#9e9e9e", appBg: "#f4f7fb", header: "#f5f5f5", card: "#fafafa", hero: "#eef5ff",
  terminalBg: "#1a1a2e", terminalOk: "#00ff88", terminalWarn: "#ffaa00", terminalDim: "#888", terminalText: "#ccc",
  successSoft: "#e8f5e9", dangerSoft: "#ffebee", probabilityBg: "#e0e0e0",
};
const PIE_COLORS = [COLORS.primary, COLORS.secondary, COLORS.accent, COLORS.danger, COLORS.purple, COLORS.teal, COLORS.pink, COLORS.deepPurple, COLORS.orange];
const CHART_DEFAULTS = { maxRotation: 45, maxTicksLimit: 20, tension: 0.3, pointRadius: 2, barMaxWidth: 500 };
const SUPABASE_PAGE_SIZE = Number(import.meta.env.VITE_SUPABASE_PAGE_SIZE || 1000);
const DETAIL_ROWS_OPTIONS = (import.meta.env.VITE_DETAIL_ROWS_OPTIONS || "25,50,100").split(",").map(Number);
const INITIAL_DETAIL_ROWS = Number(import.meta.env.VITE_DETAIL_ROWS || DETAIL_ROWS_OPTIONS[0]);
const DRAWER_WIDTH = 240;
const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "data", label: "Datos" },
  { id: "ml", label: "ML Insights" },
];
const CHART_TABS = [
  { id: "overview", label: "Resumen" },
  { id: "borough", label: "Distritos" },
  { id: "category", label: "Categorías" },
  { id: "trend", label: "Temporal" },
  { id: "minor", label: "Subcategorías" },
  { id: "matrix", label: "Año/Distrito" },
];
const TEXT = {
  loading: "Cargando...", missingEnv: "Faltan variables de entorno", dashboardTitle: "London Crime Dashboard",
  cleanRecords: "Registros Limpios", leadingDistrict: "Distrito Líder", mainCategory: "Categoría Principal",
  filters: "Filtros", district: "Distrito", category: "Categoría",
  year: "Año", all: "Todos", allF: "Todas", crimes: "Crímenes", borough: "Borough",
  crimesByDistrict: "Crímenes por Distrito", proportionByCategory: "Proporción por Categoría",
  temporalTrend: "Tendencia Temporal", topSubcategories: "Top 10 Subcategorías",
  crimesByDistrictAndYear: "Crímenes por Distrito y Año",
  detailedData: "Datos Detallados", noFilteredData: "No hay datos con los filtros seleccionados.",
  exportFiltered: "Exportar CSV Filtrado",
  exportAggregated: "Exportar CSV Agregado",
  exportComplete: "Exportar CSV Completo",
  exporting: "Exportando...",
  dataAggregated: "Datos Agregados",
  crimesByBoroughTable: "Crímenes por Distrito",
  top10Subcategories: "Top 10 Subcategorías",
  temporalTrendTable: "Tendencia Temporal (Mes a Mes)",
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
const ML_API_URL = import.meta.env.VITE_ML_API_URL || "http://localhost:8000";

function groupBy(arr, key) {
  return arr.reduce((acc, row) => {
    acc[row[key]] = (acc[row[key]] || 0) + Number(row.total_crimes);
    return acc;
  }, {});
}

function sortedEntries(obj) {
  return Object.entries(obj).sort((a, b) => b[1] - a[1]);
}

function exportCsv(filename, records) {
  if (!records.length) return;
  const headers = Object.keys(records[0]);
  const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const csv = [headers.join(","), ...records.map((row) => headers.map((h) => escape(row[h])).join(","))].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterBorough, setFilterBorough] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterYear, setFilterYear] = useState("");
  const [mlMetrics, setMlMetrics] = useState(null);
  const [pipelineStats, setPipelineStats] = useState(null);
  const [pipelineLogs, setPipelineLogs] = useState(null);
  const [logsOpen, setLogsOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [activePage, setActivePage] = useState("dashboard");
  const [chartTab, setChartTab] = useState("overview");
  const [tablePage, setTablePage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(INITIAL_DETAIL_ROWS);
  const [toast, setToast] = useState(null);

  // Predictor state
  const [predBorough, setPredBorough] = useState("");
  const [predCategory, setPredCategory] = useState("");
  const [predSubcategory, setPredSubcategory] = useState("");
  const [predYear, setPredYear] = useState(2016);
  const [predMonth, setPredMonth] = useState(1);
  const [predResult, setPredResult] = useState(null);
  const [predLoading, setPredLoading] = useState(false);
  const [predError, setPredError] = useState(null);

  const notify = (message, severity = "error") => setToast({ message, severity });

  const theme = useMemo(() => createTheme({
    palette: {
      mode: "light",
      primary: { main: COLORS.primary },
      secondary: { main: COLORS.secondary },
      background: { default: SURFACE_COLORS.appBg, paper: "#fff" },
    },
    shape: { borderRadius: 10 },
    components: {
      MuiCard: { styleOverrides: { root: { boxShadow: "0 8px 24px rgba(15,23,42,.08)", transition: "transform .15s ease, box-shadow .15s ease", "&:hover": { transform: "translateY(-2px)", boxShadow: "0 14px 30px rgba(15,23,42,.12)" } } } },
      MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    },
  }), []);

  useEffect(() => {
    async function fetchRows() {
      setLoading(true);
      if (!supabaseUrl || !supabaseKey) {
        setRows([]);
        setLoading(false);
        return;
      }
      // Supabase caps responses at 1000 rows per request,
      // so we paginate sequentially with retry to avoid rate limits.
      const PAGE_SIZE = SUPABASE_PAGE_SIZE;

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

      // Fetch remaining pages sequentially with retry
      const MAX_RETRIES = 3;
      async function fetchPage(from, to, attempt = 0) {
        const { data, error } = await supabase
          .from(TABLE_NAME)
          .select("*")
          .order("borough", { ascending: true })
          .range(from, to);
        if (error && attempt < MAX_RETRIES) {
          await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
          return fetchPage(from, to, attempt + 1);
        }
        return data;
      }

      let allRows = [firstPage];
      // fetch in series instead of parallel to avoid Supabase rate limits
      for (let i = 0; i < ranges.length; i += 1) {
        const { from, to } = ranges[i];
        const data = await fetchPage(from, to);
        if (data) allRows.push(data);
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

  useEffect(() => {
    fetch("/pipeline_stats.json")
      .then((r) => r.json())
      .then(setPipelineStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch("/pipeline_logs.json")
      .then((r) => r.json())
      .then(setPipelineLogs)
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
  const pagedRows = filtered.slice(tablePage * rowsPerPage, tablePage * rowsPerPage + rowsPerPage);

  // Export Functions
  const exportToExcelFiltered = async () => {
    setExporting(true);
    try {
      const wsData = filtered.map((row) => ({
        "Borough": row.borough,
        "Major Category": row.major_category,
        "Minor Category": row.minor_category,
        "Year": row.year,
        "Month": row.month,
        "Total Crimes": row.total_crimes,
        "Date": row.date || "",
      }));
      exportCsv(`london_crime_filtered_${new Date().toISOString().split('T')[0]}.csv`, wsData);
    } catch (error) {
      console.error("Error exporting filtered data:", error);
      notify("Error al exportar datos filtrados");
    } finally {
      setExporting(false);
    }
  };

  const exportToExcelAggregated = async () => {
    setExporting(true);
    try {
      const boroughData = Object.entries(boroughTotals).map(([name, value]) => ({
        "Type": TEXT.crimesByBoroughTable,
        "Borough": name,
        "Minor Category": "",
        "Date": "",
        "Total Crimes": value,
      }));

      const topMinorData = topMinor.map(([category, count]) => ({
        "Type": TEXT.top10Subcategories,
        "Borough": "",
        "Minor Category": category,
        "Date": "",
        "Total Crimes": count,
      }));

      const trendData = trendChart.map((item) => ({
        "Type": TEXT.temporalTrendTable,
        "Borough": "",
        "Minor Category": "",
        "Date": item.date,
        "Total Crimes": item.crimenes,
      }));

      exportCsv(`london_crime_aggregated_${new Date().toISOString().split('T')[0]}.csv`, [...boroughData, ...topMinorData, ...trendData]);
    } catch (error) {
      console.error("Error exporting aggregated data:", error);
      notify("Error al exportar datos agregados");
    } finally {
      setExporting(false);
    }
  };

  const exportToExcelComplete = async () => {
    setExporting(true);
    try {
      const wsData = rows.map((row) => ({
        "Borough": row.borough,
        "Major Category": row.major_category,
        "Minor Category": row.minor_category,
        "Year": row.year,
        "Month": row.month,
        "Total Crimes": row.total_crimes,
        "Date": row.date || "",
      }));
      exportCsv(`london_crime_complete_${new Date().toISOString().split('T')[0]}.csv`, wsData);
    } catch (error) {
      console.error("Error exporting complete data:", error);
      notify("Error al exportar dataset completo");
    } finally {
      setExporting(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "background.default" }}>
        <AppBar position="fixed" elevation={0} sx={{ width: { md: `calc(100% - ${DRAWER_WIDTH}px)` }, ml: { md: `${DRAWER_WIDTH}px` }, background: "linear-gradient(90deg, #0f4c81 0%, #1976d2 55%, #2f80ed 100%)" }}>
          <Toolbar sx={{ gap: 2 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ flexGrow: 1 }}>{TEXT.dashboardTitle}</Typography>
            <Chip label="Estimador histórico" size="small" sx={{ bgcolor: "rgba(255,255,255,.16)", color: "white" }} />
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" },
            display: { xs: "none", md: "block" },
          }}
        >
          <Toolbar>
            <Typography variant="subtitle1" fontWeight="bold">London Crime</Typography>
          </Toolbar>
          <Divider />
          <List>
            {NAV_ITEMS.map((item) => (
              <ListItemButton key={item.id} selected={activePage === item.id} onClick={() => setActivePage(item.id)}>
                {item.label}
              </ListItemButton>
            ))}
          </List>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, width: { md: `calc(100% - ${DRAWER_WIDTH}px)` } }}>
          <Toolbar />
          <Container maxWidth="xl" sx={{ py: 4, px: { xs: 1, sm: 2, md: 3 } }}>
            <Box sx={{ display: { xs: "flex", md: "none" }, gap: 1, mb: 2, overflowX: "auto" }}>
              {NAV_ITEMS.map((item) => (
                <Button key={item.id} variant={activePage === item.id ? "contained" : "outlined"} onClick={() => setActivePage(item.id)} size="small">
                  {item.label}
                </Button>
              ))}
            </Box>
            <Paper sx={{ mb: 3, p: { xs: 2, md: 3 }, background: `linear-gradient(135deg, ${SURFACE_COLORS.hero} 0%, #ffffff 70%)`, border: "1px solid rgba(25,118,210,.12)" }}>
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                {TEXT.dashboardTitle}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Panel tipo Power BI para explorar crimen histórico, DataOps y estimaciones ML sin prometer predicción futura.
              </Typography>
            </Paper>
            <Box sx={{ display: activePage === "dashboard" ? "block" : "none" }}>

      {/* Pipeline Overview — 4 cards explaining data flow */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Stage 1: Raw BigQuery records */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderTop: 3, borderColor: SURFACE_COLORS.raw }}>
            <CardContent sx={{ py: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1 }}>Fase 1 — BigQuery</Typography>
              <Typography variant="body2" color="text.secondary">Datos Crudos (LSOA)</Typography>
              <Typography variant="h4" fontWeight="bold">~3,000,000</Typography>
              <Typography variant="caption" color="text.secondary">Registros a nivel LSOA (~1500 hab.) del dataset público de Londres</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Stage 2: Cleaning — show filtering steps */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderTop: 3, borderColor: COLORS.accent }}>
            <CardContent sx={{ py: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1 }}>Fase 2 — Limpieza</Typography>
              <Typography variant="body2" color="text.secondary">Registros Eliminados</Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
                {[
                  { label: "Nulos", color: COLORS.danger },
                  { label: "Meses inválidos", color: COLORS.accent },
                  { label: "Años fuera de rango", color: COLORS.accent },
                  { label: "Valores negativos", color: COLORS.danger },
                  { label: "Duplicados", color: COLORS.accent },
                  { label: "Normalización", color: COLORS.primary },
                ].map((tag) => (
                  <Box key={tag.label} sx={{ bgcolor: tag.color + "18", color: tag.color, borderRadius: 0.5, px: 0.8, py: 0.1, fontSize: 10, fontWeight: "medium", display: "inline-block" }}>
                    {tag.label}
                  </Box>
                ))}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
                Se eliminan registros con datos inválidos antes de agregar
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Stage 3: Aggregation result */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderTop: 3, borderColor: COLORS.secondary }}>
            <CardContent sx={{ py: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1 }}>Fase 3 — Agregación</Typography>
              <Typography variant="body2" color="text.secondary">Registros Limpios</Typography>
              <Typography variant="h4" fontWeight="bold">{rows.length.toLocaleString()}</Typography>
              <Typography variant="caption" color="text.secondary">
                Agrupados por (borough, major_category, minor_category, year, month). Cada fila = suma de crímenes en ese grupo.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Stage 4: Total Crimes — the actual crime count */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderTop: 3, borderColor: COLORS.danger }}>
            <CardContent sx={{ py: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1 }}>Total Reales</Typography>
              <Typography variant="body2" color="text.secondary">Crímenes (Suma)</Typography>
              <Typography variant="h4" fontWeight="bold" sx={{ color: COLORS.danger }}>{totalCrimes.toLocaleString()}</Typography>
              <Typography variant="caption" color="text.secondary">
                Suma de total_crimes en TODAS las filas. ¿Por qué no 3M? Los ~3M son filas LSOA (cada una con ~0.5 crímenes promedio), no crímenes individuales. 1.4M es la suma real.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top-level snapshot cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">{TEXT.leadingDistrict}</Typography>
            <Typography variant="h4" fontWeight="bold">{topBorough ? topBorough[0] : "-"}</Typography>
            <Typography variant="caption" color="text.secondary">{topBorough ? topBorough[1].toLocaleString() + " crímenes (" + (topBorough[1]/totalCrimes*100).toFixed(1) + "% del total)" : ""}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">{TEXT.mainCategory}</Typography>
            <Typography variant="h4" fontWeight="bold">{topCategory ? topCategory[0] : "-"}</Typography>
            <Typography variant="caption" color="text.secondary">{topCategory ? topCategory[1].toLocaleString() + " crímenes (" + (topCategory[1]/totalCrimes*100).toFixed(1) + "% del total)" : ""}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">Años Cubiertos</Typography>
            <Typography variant="h4" fontWeight="bold">{yearRange}</Typography>
            <Typography variant="caption" color="text.secondary">{distinctBoroughs.length} distritos · {distinctCategories.length} categorías</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      {/* Pipeline Logs — collapsible section */}
      <Paper sx={{ mb: 4, overflow: "hidden" }}>
        <Box sx={{ display: "flex", alignItems: "center", px: 2, py: 1.5, bgcolor: SURFACE_COLORS.header, cursor: "pointer" }} onClick={() => setLogsOpen(!logsOpen)}>
          <TimelineIcon sx={{ mr: 1, fontSize: 20, color: "text.secondary" }} />
          <Typography variant="subtitle2" fontWeight="bold" sx={{ flexGrow: 1 }}>
            Pipeline ETL — Resumen de Ejecución
          </Typography>
          {pipelineLogs?.production_runs?.[0] && (
            <>
              <Chip label={pipelineLogs.production_runs[0].mode} size="small" color={pipelineLogs.production_runs[0].mode === "Produccion" ? "success" : "warning"} sx={{ mr: 1, height: 20, fontSize: 11 }} />
              <Typography variant="caption" color="text.secondary" sx={{ mr: 2 }}>
                {pipelineLogs.production_runs[0].duration_seconds.toFixed(1)}s · {pipelineLogs.production_runs[0].total_records_in.toLocaleString()} → {pipelineLogs.production_runs[0].total_records_out.toLocaleString()}
              </Typography>
            </>
          )}
          <IconButton size="small">{logsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}</IconButton>
        </Box>

        <Collapse in={logsOpen}>
          {pipelineLogs ? (
            <Box sx={{ px: 2, py: 2 }}>
              {/* Run summary */}
              {pipelineLogs.production_runs?.map((run, ri) => (
                <Box key={ri} sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1, fontSize: 10 }}>Ejecución: {run.run_id}</Typography>
                  <Grid container spacing={1.5} sx={{ mt: 0.5 }}>
                    {run.stages.map((s, si) => (
                      <Grid item xs={6} sm={4} md={2} key={si}>
                        <Card variant="outlined" sx={{ bgcolor: SURFACE_COLORS.card }}>
                          <CardContent sx={{ py: 1, px: 1.5, "&:last-child": { pb: 1 } }}>
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10, lineHeight: 1.2, display: "block" }}>{s.stage}</Typography>
                            <Typography variant="body2" fontWeight="bold">{s.duration_s.toFixed(1)}s</Typography>
                            {s.records_in && <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>{s.records_in.toLocaleString()} → {s.records_out?.toLocaleString() || "—"}</Typography>}
                            {s.reduction_pct && <Typography variant="caption" color="primary" sx={{ fontSize: 10 }}>-{s.reduction_pct}%</Typography>}
                            {s.records_loaded && <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>{s.records_loaded.toLocaleString()} registros</Typography>}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              ))}

              {/* Cleaning steps table */}
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1, fontSize: 10 }}>Pasos de Limpieza</Typography>
              <Table size="small" sx={{ mt: 0.5, mb: 2 }}>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: "bold", fontSize: 11, py: 0.5 }}>Paso</TableCell>
                    <TableCell sx={{ fontWeight: "bold", fontSize: 11, py: 0.5 }} align="right">Registros Afectados</TableCell>
                    <TableCell sx={{ fontWeight: "bold", fontSize: 11, py: 0.5 }}>Detalle</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pipelineLogs.cleaning_details.map((step, i) => (
                    <TableRow key={i}>
                      <TableCell sx={{ fontSize: 11, py: 0.5 }}>{step.step}</TableCell>
                      <TableCell sx={{ fontSize: 11, py: 0.5 }} align="right">
                        {step.count !== undefined ? (
                          <Chip label={step.count.toLocaleString()} size="small" color={step.count > 0 ? "warning" : "default"} sx={{ height: 18, fontSize: 10 }} />
                        ) : "—"}
                      </TableCell>
                      <TableCell sx={{ fontSize: 11, py: 0.5, color: "text.secondary" }}>{step.detail}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Recent log entries */}
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 1, fontSize: 10 }}>Últimos Eventos del Pipeline</Typography>
              <Box sx={{ bgcolor: SURFACE_COLORS.terminalBg, color: SURFACE_COLORS.terminalOk, borderRadius: 1, p: 1.5, mt: 0.5, fontFamily: "monospace", fontSize: 11, maxHeight: 200, overflowY: "auto" }}>
                {pipelineLogs.recent_entries.map((e, i) => (
                  <Box key={i} sx={{ display: "flex", gap: 1 }}>
                    <Typography variant="caption" sx={{ color: SURFACE_COLORS.terminalDim, fontFamily: "monospace", fontSize: 10, whiteSpace: "nowrap" }}>{e.ts}</Typography>
                    <Typography variant="caption" sx={{ color: e.level === "WARN" ? SURFACE_COLORS.terminalWarn : SURFACE_COLORS.terminalOk, fontFamily: "monospace", fontSize: 10, whiteSpace: "nowrap" }}>[{e.level}]</Typography>
                    <Typography variant="caption" sx={{ color: SURFACE_COLORS.terminalText, fontFamily: "monospace", fontSize: 10 }}>{e.msg}</Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          ) : (
            <Box sx={{ px: 2, py: 3, textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">No hay logs de pipeline disponibles. Ejecuta el pipeline ETL para verlos.</Typography>
            </Box>
          )}
        </Collapse>
      </Paper>

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

        {/* Export Buttons */}
        <Box sx={{ mt: 3, display: "flex", gap: 2, justifyContent: "center", flexWrap: "wrap" }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={exporting ? <CircularProgress size={20} /> : <FileDownloadIcon />}
            onClick={exportToExcelFiltered}
            disabled={filtered.length === 0 || exporting}
            size="small"
          >
            {exporting ? TEXT.exporting : TEXT.exportFiltered}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={exporting ? <CircularProgress size={20} /> : <FileDownloadIcon />}
            onClick={exportToExcelAggregated}
            disabled={rows.length === 0 || exporting}
            size="small"
          >
            {exporting ? TEXT.exporting : TEXT.exportAggregated}
          </Button>
          <Button
            variant="contained"
            color="warning"
            startIcon={exporting ? <CircularProgress size={20} /> : <FileDownloadIcon />}
            onClick={exportToExcelComplete}
            disabled={rows.length === 0 || exporting}
            size="small"
          >
            {exporting ? TEXT.exporting : TEXT.exportComplete}
          </Button>
        </Box>
      </Paper>

      <Paper sx={{ mb: 2, px: 1 }}>
        <Tabs value={chartTab} onChange={(_, value) => setChartTab(value)} variant="scrollable" scrollButtons="auto" aria-label="Selector de gráficos">
          {CHART_TABS.map((tab) => <Tab key={tab.id} value={tab.id} label={tab.label} />)}
        </Tabs>
      </Paper>

      <Box sx={{ display: chartTab === "overview" || chartTab === "borough" ? "block" : "none" }}>
      <Paper sx={{ p: 2, mb: 4, borderTop: 4, borderColor: COLORS.primary }}>
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
      </Box>

      <Box sx={{ display: chartTab === "overview" || chartTab === "category" ? "block" : "none" }}>
      <Paper sx={{ p: 2, mb: 4, borderTop: 4, borderColor: COLORS.accent }}>
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
      </Box>

      <Box sx={{ display: chartTab === "overview" || chartTab === "trend" ? "block" : "none" }}>
      <Paper sx={{ p: 2, mb: 4, borderTop: 4, borderColor: COLORS.danger }}>
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
      </Box>

      <Box sx={{ display: chartTab === "overview" || chartTab === "minor" ? "block" : "none" }}>
      <Paper sx={{ p: 2, mb: 4, borderTop: 4, borderColor: COLORS.secondary }}>
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
      </Box>

      <Box sx={{ display: chartTab === "overview" || chartTab === "matrix" ? "block" : "none" }}>
      <Paper sx={{ p: 2, mb: 4, borderTop: 4, borderColor: COLORS.teal }}>
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
      </Box>

            </Box>

            <Box sx={{ display: activePage === "data" ? "block" : "none" }}>
      <Typography variant="h6" gutterBottom>{TEXT.detailedData}</Typography>
      {filtered.length === 0 ? (
        <Alert severity="info">{TEXT.noFilteredData}</Alert>
      ) : (
        <>
          <Box sx={{ mb: 2, display: "flex", justifyContent: "flex-end" }}>
            <Button
              variant="outlined"
              color="primary"
              startIcon={exporting ? <CircularProgress size={20} /> : <FileDownloadIcon />}
              onClick={exportToExcelFiltered}
              disabled={exporting}
              size="small"
            >
              {exporting ? TEXT.exporting : TEXT.exportFiltered}
            </Button>
          </Box>
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
                {pagedRows.map((row, idx) => (
                  <TableRow key={idx}>
                    {columns.map((col) => (
                      <TableCell key={col}>{row[col] != null ? String(row[col]) : "-"}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={filtered.length}
            page={tablePage}
            onPageChange={(_, page) => setTablePage(page)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => { setRowsPerPage(Number(e.target.value)); setTablePage(0); }}
            rowsPerPageOptions={DETAIL_ROWS_OPTIONS}
          />
        </>
      )}

            </Box>

            <Box sx={{ display: activePage === "ml" ? "block" : "none" }}>
      {/* ML Insights Section */}
      <Box sx={{ mt: 6, mb: 2 }}>
        <Typography variant="h5" fontWeight="bold" gutterBottom align="center">
          ML Insights — Perfil Histórico de Criminalidad
        </Typography>
        {mlMetrics && (
          <>
            <Typography variant="subtitle2" align="center" color="text.secondary" gutterBottom>
              Modelo: {mlMetrics.model} — Estima si la incidencia supera la mediana histórica global (3 delitos/mes)
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
                      <Box sx={{ bgcolor: SURFACE_COLORS.successSoft, border: 1, borderColor: "success.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.true_negatives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">VN</Typography></Box>
                      <Box sx={{ bgcolor: SURFACE_COLORS.dangerSoft, border: 1, borderColor: "error.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.false_positives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">FP</Typography></Box>
                      <Typography variant="caption" sx={{ fontWeight: "bold" }}>Real Alto</Typography>
                      <Box sx={{ bgcolor: SURFACE_COLORS.dangerSoft, border: 1, borderColor: "error.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.false_negatives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">FN</Typography></Box>
                      <Box sx={{ bgcolor: SURFACE_COLORS.successSoft, border: 1, borderColor: "success.main", borderRadius: 1, px: 2, py: 1 }}><Typography align="center" fontWeight="bold">{mlMetrics.true_positives.toLocaleString()}</Typography><Typography variant="caption" display="block" align="center">VP</Typography></Box>
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

      {/* Historical Estimator */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom fontWeight="bold">
          Estimador Histórico — Delitos Estimados e Incidencia
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Selecciona distrito, categoría, mes y año para estimar el perfil histórico de delitos. Esto NO es una predicción del futuro: el modelo aprende patrones del dataset histórico y estima cuántos delitos cabría esperar según el perfil aprendido. Los datos cubren 2008-2016.
        </Typography>

        <Grid container spacing={2} alignItems="flex-end">
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Distrito</InputLabel>
              <Select value={predBorough} label="Distrito" onChange={(e) => { setPredBorough(e.target.value); setPredResult(null); }}>
                <MenuItem value="">—</MenuItem>
                {distinctBoroughs.map((b) => <MenuItem key={b} value={b}>{b}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Categoría</InputLabel>
              <Select value={predCategory} label="Categoría" onChange={(e) => { setPredCategory(e.target.value); setPredResult(null); }}>
                <MenuItem value="">—</MenuItem>
                {distinctCategories.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Subcategoría</InputLabel>
              <Select value={predSubcategory} label="Subcategoría" onChange={(e) => { setPredSubcategory(e.target.value); setPredResult(null); }}>
                <MenuItem value="">—</MenuItem>
                {[...new Set(rows.filter(r => !predCategory || r.major_category === predCategory).map(r => r.minor_category))].sort().map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={4} sm={3} md={1.5}>
            <FormControl fullWidth size="small">
              <InputLabel>Año</InputLabel>
              <Select value={predYear} label="Año" onChange={(e) => { setPredYear(Number(e.target.value)); setPredResult(null); }}>
                {distinctYears.map((y) => <MenuItem key={y} value={y}>{y}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={4} sm={3} md={1.5}>
            <FormControl fullWidth size="small">
              <InputLabel>Mes</InputLabel>
              <Select value={predMonth} label="Mes" onChange={(e) => { setPredMonth(Number(e.target.value)); setPredResult(null); }}>
                {Array.from({ length: 12 }, (_, i) => (
                  <MenuItem key={i + 1} value={i + 1}>{String(i + 1).padStart(2, "0")}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={4} sm={3} md={1}>
            <Button
              variant="contained"
              fullWidth
              disabled={!predBorough || !predCategory || !predSubcategory || predLoading}
              onClick={async () => {
                setPredLoading(true);
                setPredError(null);
                setPredResult(null);
                try {
                  const resp = await fetch(ML_API_URL + "/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      borough: predBorough,
                      major_category: predCategory,
                      minor_category: predSubcategory,
                      year: predYear,
                      month: predMonth,
                    }),
                  });
                  if (!resp.ok) throw new Error(await resp.text());
                  setPredResult(await resp.json());
                } catch (e) {
                  setPredError(e.message);
                } finally {
                  setPredLoading(false);
                }
              }}
            >
              {predLoading ? <CircularProgress size={18} /> : "Estimar"}
            </Button>
          </Grid>
        </Grid>

        {/* Prediction result */}
        {predResult && (
          <Box sx={{ mt: 2, p: 2, bgcolor: predResult.prediction === 1 ? SURFACE_COLORS.dangerSoft : SURFACE_COLORS.successSoft, borderRadius: 1 }}>
            <Typography variant="caption" color="text.secondary">Delitos estimados</Typography>
            <Typography variant="h4" fontWeight="bold">
              {predResult.predicted_crimes} delitos
            </Typography>
            <Typography variant="h5" fontWeight="bold" sx={{ color: predResult.prediction === 1 ? COLORS.danger : COLORS.secondary }}>
              {predResult.prediction === 1 ? "ALTA INCIDENCIA" : "BAJA INCIDENCIA"}
            </Typography>
            <Box sx={{ display: "flex", gap: 3, mt: 1, flexWrap: "wrap" }}>
              <Box>
                <Typography variant="caption" color="text.secondary">Prob. Alta</Typography>
                <Typography variant="h6" fontWeight="bold" sx={{ color: COLORS.danger }}>{(predResult.probability_high * 100).toFixed(1)}%</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Prob. Baja</Typography>
                <Typography variant="h6" fontWeight="bold" sx={{ color: COLORS.secondary }}>{(predResult.probability_low * 100).toFixed(1)}%</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Features</Typography>
                <Typography variant="h6" fontWeight="bold">{predResult.features_used}</Typography>
              </Box>
            </Box>
            <Alert severity="warning" sx={{ mt: 2 }}>
              <strong>Limitación importante:</strong> El modelo se entrenó con un split aleatorio 70/30, no
              respetando el orden temporal. Esto significa que "aprende" de datos futuros para estimar datos pasados,
              inflando artificialmente las métricas de accuracy (~89%) y R² (~0.94). En un escenario real de
              predicción futura, el rendimiento sería significativamente menor. La estimación refleja el perfil
              histórico aprendido, no una proyección hacia adelante.
            </Alert>
            {/* Probability bar */}
            <Box sx={{ mt: 1, width: "100%", bgcolor: SURFACE_COLORS.probabilityBg, borderRadius: 1, height: 20, position: "relative", overflow: "hidden" }}>
              <Box sx={{ width: `${(predResult.probability_high * 100).toFixed(1)}%`, bgcolor: COLORS.danger, height: "100%", transition: "width 0.5s" }} />
              <Typography variant="caption" sx={{ position: "absolute", top: 2, left: 8, fontWeight: "bold", color: "#333" }}>
                Baja: {(predResult.probability_low * 100).toFixed(0)}%
              </Typography>
              <Typography variant="caption" sx={{ position: "absolute", top: 2, right: 8, fontWeight: "bold", color: "#fff" }}>
                Alta: {(predResult.probability_high * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Box>
        )}
        {predError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Error: {predError}
          </Alert>
        )}
      </Paper>
            </Box>
          </Container>
          <Snackbar open={Boolean(toast)} autoHideDuration={4000} onClose={() => setToast(null)}>
            <Alert severity={toast?.severity || "info"} onClose={() => setToast(null)} sx={{ width: "100%" }}>
              {toast?.message}
            </Alert>
          </Snackbar>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
