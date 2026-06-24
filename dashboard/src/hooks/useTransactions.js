import { useCallback, useEffect, useState } from "react";

import { fetchTransactions } from "../services/api";
import { useInterval } from "./useInterval";

const POLL_INTERVAL_MS = 5000;

/*
 * Recupere les dernieres transactions et rafraichit automatiquement toutes
 * les 5 secondes (useInterval), pour que le dashboard reste a jour sans que
 * l'utilisateur ait besoin de recharger la page.
 *
 * On garde loading=true seulement pour le tout premier chargement : les
 * rafraichissements suivants se font en arriere-plan, sans faire clignoter
 * l'UI avec un etat "loading" a chaque poll.
 */
export function useTransactions(limit = 50) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const transactions = await fetchTransactions(limit);
      setData(transactions);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    load();
  }, [load]);

  useInterval(load, POLL_INTERVAL_MS);

  return { data, loading, error };
}
