import { AreaChart, Area, Tooltip, XAxis } from "recharts";
import { BetaParams } from "../types";
import { a } from "framer-motion/client";
import { gamma } from "mathjs";

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
    posteriors.forEach(({ name, alpha, beta }, i) => {
      point[`${i}_${name}`] = betaPDF(xVal, alpha, beta);
    });
    priors.forEach(({ name, alpha, beta }, i) => {
      point[`${i}_${name}_prior`] = betaPDF(xVal, alpha, beta);
    });
    return point;
  });

  const tooltipFormatter = (value: string, name: string) => {
    return name.endsWith("_prior")
      ? [null, null]
      : [Math.round(Number(value) * 100) / 100, name];
  };

  console.log(posteriors, priors);
  return (
    <AreaChart width={700} height={400} data={data}>
      <Tooltip />
      <XAxis
        padding={{ left: 40, right: 40 }}
        dataKey="x"
        allowDecimals={false}
      />
      {posteriors.map((dist, i) => (
        <Area
          key={`${i}_${dist.name}`}
          dataKey={`${i}_${dist.name}`}
          stroke={COLORS[i]}
          fill={COLORS[i]}
          fillOpacity={0.3}
        />
      ))}
      {priors.map((dist, i) => (
        <Area
          key={`${i}_${dist.name}_prior`}
          dataKey={`${i}_${dist.name}_prior`}
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
