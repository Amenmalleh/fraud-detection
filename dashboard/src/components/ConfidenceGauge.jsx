import { PolarAngleAxis, RadialBar, RadialBarChart } from "recharts";

/*
 * Jauge circulaire : une seule barre radiale dont la longueur represente la
 * confidence (0 a 1). La couleur s'adapte au niveau (rouge si risque eleve)
 * pour une lecture immediate, sans avoir a lire le chiffre.
 */
export default function ConfidenceGauge({ confidence }) {
  const percent = Math.round(confidence * 100);
  const color = confidence >= 0.5 ? "var(--fraud)" : "var(--legit)";
  const data = [{ value: percent, fill: color }];

  return (
    <div className="confidence-gauge">
      <RadialBarChart
        width={140}
        height={140}
        cx={70}
        cy={70}
        innerRadius={50}
        outerRadius={70}
        barSize={12}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
        <RadialBar background={{ fill: "var(--border)" }} dataKey="value" cornerRadius={6} />
      </RadialBarChart>
      <div className="confidence-gauge-label" style={{ color }}>
        {percent}%
      </div>
    </div>
  );
}
