const TABLE_NAME = import.meta.env.VITE_SUPABASE_TABLE_NAME || "london_crime_aggregated";

export const DB_CONFIG = {
  tableName: TABLE_NAME,
};
