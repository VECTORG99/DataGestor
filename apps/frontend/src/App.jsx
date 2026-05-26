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

ChartJS.register(
  CategoryScale, LinearScale, BarElement, ArcElement,
  PointElement, LineElement, Filler,
  Title, Tooltip, Legend
);

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

  useEffect(() => {
    async function fetchRows() {
      setLoading(true);
      if (!supabaseUrl || !supabaseKey) {
        setRows([]);
        setLoading(false);
        return;
      }
      const { data, error } = await supabase
        .from("london_crime_aggregated")
        .select("*");
      if (error) {
        setRows([]);
      } else {
        setRows(data || []);
      }
      setLoading(false);
    }
    fetchRows();
  }, []);

  if (loading) {
    return (
      <Container sx={{ py: 4 }}>
        <Typography variant="h4">Cargando...</Typography>
      </Container>
    );
  }

  if (!supabaseUrl || !supabaseKey) {
    return (
      <Container sx={{ py: 4 }}>
        <Alert severity="error">Faltan variables de entorno</Alert>
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
        London Crime Dashboard
      </Typography>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">Total Crimenes</Typography>
            <Typography variant="h4" fontWeight="bold">{totalCrimes.toLocaleString()}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">Distrito Lider</Typography>
            <Typography variant="h4" fontWeight="bold">{topBorough ? topBorough[0] : "-"}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">Categoria Principal</Typography>
            <Typography variant="h4" fontWeight="bold">{topCategory ? topCategory[0] : "-"}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card><CardContent>
            <Typography variant="body2" color="text.secondary">Registros Filtrados</Typography>
            <Typography variant="h4" fontWeight="bold">{filtered.length.toLocaleString()}</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: 4 }}>
        <Typography variant="subtitle1" fontWeight="bold" gutterBottom align="center">
          Filtros
        </Typography>
        <Grid container spacing={2} justifyContent="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Distrito</InputLabel>
              <Select value={filterBorough} label="Distrito" onChange={(e) => setFilterBorough(e.target.value)}>
                <MenuItem value="">Todos</MenuItem>
                {distinctBoroughs.map((b) => <MenuItem key={b} value={b}>{b}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Categoria</InputLabel>
              <Select value={filterCategory} label="Categoria" onChange={(e) => setFilterCategory(e.target.value)}>
                <MenuItem value="">Todas</MenuItem>
                {distinctCategories.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Anio</InputLabel>
              <Select value={filterYear} label="Anio" onChange={(e) => setFilterYear(e.target.value)}>
                <MenuItem value="">Todos</MenuItem>
                {distinctYears.map((y) => <MenuItem key={y} value={y}>{y}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Crimenes por Distrito</Typography>
        <Bar
          data={{
            labels: boroughChart.map((r) => r.name),
            datasets: [{
              label: "Crimenes",
              data: boroughChart.map((r) => r.crimenes),
              backgroundColor: "#1976d2",
            }],
          }}
          options={{
            responsive: true,
            indexAxis: "x",
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { maxRotation: 45 } } },
          }}
        />
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Proporcion por Categoria</Typography>
        <Box sx={{ maxWidth: 500, mx: "auto" }}>
          <Pie
            data={{
              labels: pieData.map((r) => r.name),
              datasets: [{
                data: pieData.map((r) => r.value),
                backgroundColor: ["#1976d2", "#388e3c", "#f57c00", "#d32f2f", "#7b1fa2", "#00796b", "#c2185b", "#512da8", "#e64a19"],
              }],
            }}
            options={{ responsive: true, plugins: { legend: { position: "bottom" } } }}
          />
        </Box>
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Tendencia Temporal</Typography>
        <Line
          data={{
            labels: trendChart.map((r) => r.date),
            datasets: [{
              label: "Crimenes",
              data: trendChart.map((r) => r.crimenes),
              borderColor: "#d32f2f",
              backgroundColor: "rgba(211,47,47,0.1)",
              fill: true,
              tension: 0.3,
              pointRadius: 2,
            }],
          }}
          options={{
            responsive: true,
            scales: { x: { ticks: { maxRotation: 45, maxTicksLimit: 20 } } },
          }}
        />
      </Paper>

      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="h6" gutterBottom>Top 10 Subcategorias</Typography>
        <Bar
          data={{
            labels: topMinor.map((r) => r[0]),
            datasets: [{
              label: "Crimenes",
              data: topMinor.map((r) => r[1]),
              backgroundColor: "#388e3c",
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
        <Typography variant="h6" gutterBottom>Crimenes por Distrito y Anio</Typography>
        <Box sx={{ overflowX: "auto" }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold" }}>Borough</TableCell>
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

      <Typography variant="h6" gutterBottom>Datos Detallados</Typography>
      {filtered.length === 0 ? (
        <Alert severity="info">No hay datos con los filtros seleccionados.</Alert>
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
    </Container>
  );
}
