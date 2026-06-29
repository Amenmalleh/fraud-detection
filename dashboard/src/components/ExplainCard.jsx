import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

/*
 * Affiche les features qui ont le plus pese dans la decision du modele
 * (renvoyees par POST /explain). N'est rendu par PredictForm qu'apres une
 * prediction reussie : pas besoin de gerer ici un etat "vide", le parent
 * s'en occupe deja en ne montant ce composant qu'au bon moment.
 */
export default function ExplainCard({ explanation }) {
  const { prediction, explanation: features, interpretation } = explanation;
  const color = prediction.is_fraud ? "var(--fraud)" : "var(--legit)";

  // Recharts dessine les barres de bas en haut par defaut : on inverse la
  // liste pour garder la feature la plus importante en haut du graphe.
  const chartData = [...features].reverse();

  return (
    <div className="explain-card">
      <h4>Pourquoi cette décision ?</h4>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis type="number" stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="feature" stroke="var(--text-muted)" width={45} tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)" }}
            formatter={(value) => value.toFixed(4)}
          />
          <Bar dataKey="importance">
            {chartData.map((entry) => (
              <Cell key={entry.feature} fill={color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="explain-card-interpretation">{interpretation}</p>
    </div>
  );
}
