import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import Container from '@mui/material/Container';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRows() {
      setLoading(true);
      // Ajusta "mi_tabla" por el nombre real de la tabla limpia que quieres mostrar:
      const { data, error } = await supabase
        .from('london_crime_aggregated')
        .select('*');
      if (error) {
        setRows([]);
      } else {
        setRows(data);
      }
      setLoading(false);
    }
    fetchRows();
  }, []);

  // Detecta columnas
  const columns = rows[0] ? Object.keys(rows[0]) : [];

  return (
    <Container>
      <Typography variant="h3" gutterBottom>Vista de datos limpios</Typography>
      {loading ? <div>Cargando…</div> :
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                {columns.map((col) => <TableCell key={col}>{col}</TableCell>)}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row, idx) => (
                <TableRow key={idx}>
                  {columns.map((col) => (
                    <TableCell key={col}>{row[col]+""}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      }
    </Container>
  );
}
