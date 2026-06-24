import { AlertTriangle } from "lucide-react";

/*
 * Ne s'affiche que si la transaction la plus recente a ete classee comme
 * fraude. Retourner `null` est la facon standard en React de "ne rien
 * afficher" sans casser le rendu du parent (App.jsx peut toujours placer ce
 * composant dans son JSX, qu'il y ait ou non quelque chose a montrer).
 */
export default function AlertBanner({ latestTransaction }) {
  if (!latestTransaction || !latestTransaction.is_fraud) return null;

  return (
    <div className="alert-banner">
      <AlertTriangle size={20} />
      <span>
        Fraude détectée : <strong>{latestTransaction.amount.toFixed(2)} €</strong> — confiance{" "}
        <strong>{(latestTransaction.confidence * 100).toFixed(1)}%</strong>
      </span>
    </div>
  );
}
