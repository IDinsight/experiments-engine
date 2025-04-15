import {
  AreaChart,
  Area,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";
import { BetaParams, GaussianParams } from "../../types";
import { gamma } from "mathjs";
import * as d3 from "d3-scale-chromatic";

const COLORMAP = d3.interpolateSpectral;

// Beta-Binary Distribution
const lngamma = (x: number): number => {
  if (typeof x !== "number" || isNaN(x) || x <= 0) {
    return NaN;
  }
  return Math.log(gamma(x));
};

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
  const num_arms = posteriors.length;
  const COLORS = Array.from({ length: num_arms }, (_, i) =>
    COLORMAP(i / num_arms)
  );

  // Define the range of x-values
  const x = Array.from({ length: 100 }, (_, i) => i / 100);
  const xlabel = Array.from({ length: 10 }, (_, i) => i / 10);

  const data = x.map((xVal) => {
    const point: { x: number; [key: string]: number } = { x: xVal };

    const posteriorPDFs = posteriors.map(({ alpha, beta }) =>
      betaPDF(xVal, alpha, beta)
    );

    posteriors.forEach(({ name }, i) => {
      point[`${name}`] = posteriorPDFs[i];
    });

    const priorPDFs = priors.map(({ alpha, beta }) =>
      betaPDF(xVal, alpha, beta)
    );

    priors.forEach(({ name }, i) => {
      point[`Prior - ${i}_${name}`] = priorPDFs[i];
    });
    return point;
  });

  const tooltipFormatter = (value: string, name: string) => {
    return [Number(value).toFixed(2), name];
  };

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, bottom: 15, left: 10 }}
          width={undefined}
          height={undefined}
        >
          <XAxis
            // padding={{ left: 40, right: 40 }}
            dataKey="x"
            allowDecimals={true}
            ticks={xlabel}
            domain={[0, 1]}
            label={{
              value: "Arm parameter",
              position: "insideBottom",
              offset: -10,
            }}
          />
          <YAxis
            // padding={{ top: 20, bottom: 20 }}
            allowDecimals={true}
            tick={false}
            domain={[0, 1]}
            label={{ value: "Density", angle: -90, position: "insideLeft" }}
          />
          <Tooltip formatter={tooltipFormatter} />

          {posteriors.map((dist, i) => (
            <Area
              key={`${i}: ${dist.name}`}
              dataKey={`${dist.name}`}
              stroke={COLORS[i]}
              fill={COLORS[i]}
              fillOpacity={0.3}
            />
          ))}
          {priors.map((dist, i) => (
            <Area
              key={`Prior - ${i}_${dist.name}`}
              dataKey={`Prior - ${i}_${dist.name}`}
              stroke={COLORS[i]}
              strokeDasharray="5 5"
              fill={undefined}
              fillOpacity={0.1}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Normal distribution

const lnNormalPDF = (x: number, m: number, s: number): number => {
  const normalizer = -0.5 * Math.log(2 * Math.PI) - Math.log(s);
  const exponent = -0.5 * Math.pow((x - m) / s, 2);
  return normalizer + exponent;
};

const normalPDF = (x: number, m: number, s: number): number => {
  return Math.exp(lnNormalPDF(x, m, s));
};

const NormalLineChart = ({
  priors,
  posteriors,
}: {
  priors: GaussianParams[];
  posteriors: GaussianParams[];
}) => {
  const num_arms = posteriors.length;
  const COLORS = Array.from({ length: num_arms }, (_, i) =>
    COLORMAP(i / num_arms)
  );

  // Define the range of x-values
  const x = Array.from({ length: 1000 }, (_, i) => -5 + (i * 10) / 1000);
  const xlabel = Array.from({ length: 10 }, (_, i) => -5 + (i * 10) / 10);

  const data = x.map((xVal) => {
    const point: { x: number; [key: string]: number } = { x: xVal };

    const posteriorPDFs = posteriors.map(({ mu, sigma }) =>
      normalPDF(xVal, mu, sigma)
    );

    posteriors.forEach(({ name }, i) => {
      point[`Posterior - ${i}_${name}`] = posteriorPDFs[i];
    });

    const priorPDFs = priors.map(({ mu, sigma }) => normalPDF(xVal, mu, sigma));

    priors.forEach(({ name }, i) => {
      point[`Prior - ${i}_${name}`] = priorPDFs[i];
    });
    return point;
  });

  const tooltipFormatter = (value: string, name: string) => {
    return [Number(value).toFixed(2), name];
  };

  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, bottom: 15, left: 10 }}
        >
          <XAxis
            // padding={{ left: 40, right: 40 }}
            dataKey="x"
            allowDecimals={true}
            ticks={xlabel}
            domain={[-5, 5]}
            label={{
              value: "Arm parameter",
              position: "insideBottom",
              offset: -10,
            }}
          />
          <YAxis
            // padding={{ top: 20, bottom: 20 }}
            allowDecimals={true}
            tick={false}
            // domain={[0, 1]}
            label={{ value: "Density", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(64, 64, 64, 0.8)",
              border: "none",
              borderRadius: "4px",
              color: "white",
            }}
            formatter={tooltipFormatter}
          />

          {posteriors.map((dist, i) => (
            <Area
              key={`Posterior - ${i}_${dist.name}`}
              dataKey={`Posterior - ${i}_${dist.name}`}
              stroke={COLORS[i]}
              fill={COLORS[i]}
              fillOpacity={0.3}
            />
          ))}
          {priors.map((dist, i) => (
            <Area
              key={`Prior - ${i}_${dist.name}`}
              dataKey={`Prior - ${i}_${dist.name}`}
              stroke={COLORS[i]}
              strokeDasharray="5 5"
              fill={undefined}
              fillOpacity={0.1}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export { BetaLineChart, NormalLineChart };
