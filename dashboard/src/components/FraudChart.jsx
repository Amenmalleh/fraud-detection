import { useMemo } from "react";
import { format, parseISO } from "date-fns";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/*
 * On recoit la liste brute des transactions et on la regroupe nous-memes par
 * heure (HH:00) cote client, plutot que de demander un nouvel endpoint
 * d'agregation au backend : pour un dashboard de cette taille (50 lignes),
 * c'est largement suffisant et ca evite de complexifier l'API.
 */
function groupByHour(transactions) {
  const buckets = new Map();

  for (const tx of transactions) {
    if (!tx.created_at) continue;
    const hour = format(parseISO(tx.created_at), "HH:00");
    const bucket = buckets.get(hour) || { hour, fraud: 0, legit: 0 };
    if (tx.is_fraud) bucket.fraud += 1;
    else bucket.legit += 1;
    buckets.set(hour, bucket);
  }

  return Array.from(buckets.values()).sort((a, b) => a.hour.localeCompare(b.hour));
}

export default function FraudChart({ transactions }) {
  // useMemo : on ne recalcule l'aggregation que si la liste de transactions
  // change, pas a chaque rendu du composant.
  const chartData = useMemo(() => groupByHour(transactions), [transactions]);

  if (chartData.length === 0) {
    return <p className="empty-state">Pas encore assez de donnees pour le graphe.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis dataKey="hour" stroke="var(--text-muted)" />
        <YAxis stroke="var(--text-muted)" allowDecimals={false} />
        <Tooltip contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)" }} />
        <Legend />
        <Line type="monotone" dataKey="fraud" name="Fraudes" stroke="var(--fraud)" strokeWidth={2} />
        <Line type="monotone" dataKey="legit" name="Légitimes" stroke="var(--accent)" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
