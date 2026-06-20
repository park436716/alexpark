type Scores = {
  reputation: number;
  legal_risk: number;
  media_pressure: number;
  employee_trust: number;
  regulatory_risk: number;
  financial_risk: number;
};

export default function CrisisScoreBoard({ scores }: { scores: Scores }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {Object.entries(scores).map(([key, value]) => (
        <div key={key} className="rounded-xl border p-4">
          <div className="text-sm text-gray-500">{key}</div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="mt-2 h-2 rounded bg-gray-200">
            <div className="h-2 rounded bg-black" style={{ width: `${value}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
