import { format, parseISO } from "date-fns";

const MAX_ROWS = 20;

/*
 * Affiche les 20 dernieres transactions. On recoit la liste complete (jusqu'a
 * 50, cf. useTransactions) et on tronque ici : c'est ce composant qui decide
 * combien il affiche, pas le hook qui va chercher les donnees.
 */
export default function TransactionTable({ transactions }) {
  const rows = transactions.slice(0, MAX_ROWS);

  if (rows.length === 0) {
    return <p className="empty-state">Aucune transaction pour le moment.</p>;
  }

  return (
    <table className="transaction-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Montant</th>
          <th>Heure</th>
          <th>Statut</th>
          <th>Confiance</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((tx) => (
          <tr key={tx.id} className={tx.is_fraud ? "row-fraud" : "row-legit"}>
            <td>{String(tx.id).slice(0, 6)}</td>
            <td>{tx.amount.toFixed(2)} €</td>
            <td>{tx.created_at ? format(parseISO(tx.created_at), "HH:mm:ss") : "—"}</td>
            <td className={tx.is_fraud ? "text-fraud" : "text-legit"}>
              {tx.is_fraud ? "FRAUDE" : "LÉGITIME"}
            </td>
            <td>{(tx.confidence * 100).toFixed(1)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
