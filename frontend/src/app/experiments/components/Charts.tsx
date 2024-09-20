import { AreaChart, Area, Tooltip, XAxis } from "recharts";
import { BetaParams } from "../types";
import { a } from "framer-motion/client";
import { gamma } from "mathjs";

// Define the parameters for each Beta distribution
const betaDists: BetaParams[] = [
  { name: "arm1", alpha: 1, beta: 3 },
  { name: "arm2", alpha: 4, beta: 6 },
  { name: "arm3", alpha: 2, beta: 7 },
];

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

const lngamma = (x: number): number => Math.log(gamma(x));

const lnBetaPDF = (x: number, a: number, b: number): number => {
  const betaInv = lngamma(a + b) - lngamma(a) - lngamma(b);
  return betaInv + (a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x);
};

const betaPDF = (x: number, a: number, b: number): number => {
  return Math.exp(lnBetaPDF(x, a, b));
};

const BetaLineChart = ({
  priors,
  posteriors,
}: {
  priors: BetaParams[];
  posteriors: BetaParams[];
}) => {
  // Define the range of x-values
  const x = Array.from({ length: 100 }, (_, i) => i / 100);

  // Calculate PDFs for each distribution and store them in a format compatible with Recharts
  const data = x.map((xVal) => {
    const point: { x: number; [key: string]: number } = { x: xVal };
    posteriors.forEach(({ name, alpha, beta }) => {
      point[name] = betaPDF(xVal, alpha, beta);
    });
    priors.forEach(({ name, alpha, beta }) => {
      point[`${name}_prior`] = betaPDF(xVal, alpha, beta);
    });
    return point;
  });

  const tooltipFormatter = (value: string, name: string) => {
    return name.endsWith("_prior")
      ? [null, null]
      : [Math.round(Number(value) * 100) / 100, name];
  };

  return (
    <AreaChart width={700} height={400} data={data}>
      <Tooltip formatter={tooltipFormatter} />
      <XAxis
        padding={{ left: 40, right: 40 }}
        dataKey="x"
        allowDecimals={false}
      />
      {posteriors.map((dist, i) => (
        <Area
          key={dist.name}
          dataKey={dist.name}
          stroke={COLORS[i]}
          fill={COLORS[i]}
          fillOpacity={0.3}
        />
      ))}
      {priors.map((dist, i) => (
        <Area
          key={`${dist.name}_prior`}
          dataKey={`${dist.name}_prior`}
          stroke={COLORS[i]}
          strokeDasharray="5 5"
          fill={undefined}
          fillOpacity={0.1}
        />
      ))}
    </AreaChart>
  );
};

export { BetaLineChart };
