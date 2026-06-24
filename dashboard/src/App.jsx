import { Activity, AlertTriangle, Banknote, ShieldAlert } from "lucide-react";

import "./App.css";
import AlertBanner from "./components/AlertBanner";
import ConfidenceGauge from "./components/ConfidenceGauge";
import FraudChart from "./components/FraudChart";
import KPICard from "./components/KPICard";
import PredictForm from "./components/PredictForm";
import TransactionTable from "./components/TransactionTable";
import { useStats } from "./hooks/useStats";
import { useTransactions } from "./hooks/useTransactions";

export default function App() {
  // Chaque hook gere son propre polling (toutes les 5s) et son propre etat
  // d'erreur : App.jsx n'a qu'a lire data/loading/error, pas a savoir comment
  // les donnees sont recuperees.
  const { data: stats, loading: statsLoading, error: statsError } = useStats();
  const { data: transactions, loading: txLoading, error: txError } = useTransactions(50);

  const apiOffline = Boolean(statsError || txError);
  const latestTransaction = transactions[0] ?? null;
  const atRiskAmount = transactions.filter((tx) => tx.is_fraud).reduce((sum, tx) => sum + tx.amount, 0);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <ShieldAlert size={24} color="var(--accent)" />
          <span>FraudGuard</span>
        </div>
        <nav className="sidebar-nav">
          <span className="sidebar-nav-item active">Dashboard</span>
        </nav>
      </aside>

      <main className="main-content">
        {apiOffline && (
          <div className="api-offline-banner">
            API indisponible — vérifiez que le serveur FastAPI tourne sur :8000
          </div>
        )}

        <AlertBanner latestTransaction={latestTransaction} />

        <section className="kpi-grid">
          <KPICard
            title="Total Transactions"
            value={statsLoading ? "…" : stats?.total_transactions ?? 0}
            icon={Activity}
            color="var(--accent)"
          />
          <KPICard
            title="Total Fraudes"
            value={statsLoading ? "…" : stats?.total_fraud ?? 0}
            icon={AlertTriangle}
            color="var(--fraud)"
          />
          <KPICard
            title="Taux de Fraude"
            value={statsLoading ? "…" : `${((stats?.fraud_rate ?? 0) * 100).toFixed(2)}%`}
            icon={ShieldAlert}
            color="var(--fraud)"
          />
          <KPICard
            title="Montant à Risque"
            value={txLoading ? "…" : `${atRiskAmount.toFixed(2)} €`}
            icon={Banknote}
            color="var(--fraud)"
          />
        </section>

        <section className="panel chart-section">
          <h2>Fraudes dans le temps</h2>
          {txLoading ? <div className="skeleton skeleton-chart" /> : <FraudChart transactions={transactions} />}
        </section>

        <section className="panel table-section">
          <h2>Dernières transactions</h2>
          {txLoading ? (
            <div className="skeleton skeleton-table" />
          ) : (
            <TransactionTable transactions={transactions} />
          )}
        </section>
      </main>

      <aside className="side-panel">
        <div className="panel">
          <PredictForm />
        </div>

        {latestTransaction && (
          <div className="panel latest-confidence">
            <h4>Dernière prédiction</h4>
            <ConfidenceGauge confidence={latestTransaction.confidence} />
          </div>
        )}
      </aside>
    </div>
  );
}
