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

import { COLORS, PIE_COLORS, CHART_DEFAULTS } from "./config/chartConfig";
import { TEXT, UI_LIMITS } from "./config/text";

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

  const topMinor = sortedEntries(groupBy(filtered, "minor_category")).slice(0, UI_LIMITS.TOP_SUBCATEGORIES);

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
              {filtered.slice(0, UI_LIMITS.MAX_DISPLAY_ROWS).map((row, idx) => (
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
