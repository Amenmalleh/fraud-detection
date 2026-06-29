import { useState } from "react";

import { explainTransaction, predictTransaction } from "../services/api";
import ExplainCard from "./ExplainCard";

const V_FEATURE_COUNT = 28;

// V1..V28 viennent d'une transformation PCA sur le dataset original : un
// humain ne peut pas les "deviner" a la main. On simule donc une transaction
// plausible en tirant des valeurs aleatoires dans la plage ou se trouve la
// grande majorite des transactions reelles (-3 a +3).
function randomFeature() {
  return Number((Math.random() * 6 - 3).toFixed(3));
}

function buildRandomFeatures() {
  const features = {};
  for (let i = 1; i <= V_FEATURE_COUNT; i++) {
    features[`V${i}`] = randomFeature();
  }
  return features;
}

export default function PredictForm() {
  const [amount, setAmount] = useState(100);
  const [time, setTime] = useState(50000);
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setExplanation(null);

    const payload = {
      Amount: Number(amount),
      Time: Number(time),
      ...buildRandomFeatures(),
    };

    try {
      const prediction = await predictTransaction(payload);
      setResult(prediction);

      // Meme payload que /predict, pour que l'explication corresponde bien
      // a la transaction qui vient d'etre analysee (pas une nouvelle).
      const explainResult = await explainTransaction(payload);
      setExplanation(explainResult);
    } catch {
      setError("Impossible de contacter l'API.");
      setResult(null);
      setExplanation(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="predict-form">
      <h3>Tester une transaction</h3>
      <form onSubmit={handleSubmit}>
        <label>
          Montant (€)
          <input
            type="number"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            min="0"
            step="0.01"
          />
        </label>
        <label>
          Time (secondes)
          <input type="number" value={time} onChange={(event) => setTime(event.target.value)} min="0" />
        </label>
        <p className="predict-form-hint">
          Les features V1 à V28 sont générées aléatoirement à chaque test (elles sont anonymisées dans le
          dataset, impossible de les saisir a la main).
        </p>
        <button type="submit" disabled={loading}>
          {loading ? "Analyse..." : "Analyser la transaction"}
        </button>
      </form>

      {error && <p className="predict-form-error">{error}</p>}

      {result && (
        // La key change a chaque nouvelle prediction (transaction_id different),
        // ce qui force React a remonter ce <div> au lieu de juste mettre a jour
        // son contenu. Combine a une animation CSS sur ".predict-result" dans
        // App.css, ca relance l'animation a chaque resultat plutot qu'une seule fois.
        <div
          key={result.transaction_id}
          className={`predict-result ${result.is_fraud ? "is-fraud" : "is-legit"}`}
        >
          <div className="predict-result-label">{result.is_fraud ? "🚨 FRAUDE DÉTECTÉE" : "✅ LÉGITIME"}</div>
          <div className="predict-result-confidence">Confiance : {(result.confidence * 100).toFixed(1)}%</div>
        </div>
      )}

      {explanation && <ExplainCard explanation={explanation} />}
    </div>
  );
}
