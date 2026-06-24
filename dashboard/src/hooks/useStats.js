import { useCallback, useEffect, useState } from "react";

import { fetchStats } from "../services/api";
import { useInterval } from "./useInterval";

const POLL_INTERVAL_MS = 5000;

/* Meme logique que useTransactions, pour les statistiques globales (/stats). */
export function useStats() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const stats = await fetchStats();
      setData(stats);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useInterval(load, POLL_INTERVAL_MS);

  return { data, loading, error };
}
