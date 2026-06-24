/*
 * Carte reutilisable pour afficher une metrique (KPI). On la rend generique
 * (title/value/subtitle/color/icon en props) plutot que d'ecrire 4 fois le
 * meme JSX dans App.jsx pour les 4 indicateurs du haut de page.
 */
export default function KPICard({ title, value, subtitle, color = "var(--accent)", icon: Icon }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card-header">
        <span className="kpi-card-title">{title}</span>
        {Icon && <Icon size={18} color={color} />}
      </div>
      <div className="kpi-card-value" style={{ color }}>
        {value}
      </div>
      {subtitle && <div className="kpi-card-subtitle">{subtitle}</div>}
    </div>
  );
}
