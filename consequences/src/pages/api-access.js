import AnimatedText from "@/components/AnimatedText";
import Layout from "@/components/Layout";
import Head from "next/head";
import TransitionEffect from "@/components/TransitionEffect";
import { Section } from "@/components/Section";
import { motion } from "framer-motion";

const CodeBlock = ({ children, title }) => (
  <div className="my-6 rounded-xl overflow-hidden">
    {title && (
      <div className="bg-dark/90 dark:bg-light/10 px-4 py-2 text-sm font-mono text-light/70 dark:text-light/50 border-b border-light/10">
        {title}
      </div>
    )}
    <pre className="bg-dark/95 dark:bg-light/5 p-4 overflow-x-auto">
      <code className="text-sm font-mono text-green-400 dark:text-green-300 whitespace-pre">
        {children}
      </code>
    </pre>
  </div>
);

const EndpointCard = ({ method, path, description, children }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    viewport={{ once: true }}
    className="my-8 border border-dark/10 dark:border-light/10 rounded-xl overflow-hidden"
  >
    <div className="flex items-center gap-3 px-6 py-4 bg-dark/5 dark:bg-light/5">
      <span
        className={`px-3 py-1 rounded-md text-sm font-bold text-light ${
          method === "GET" ? "bg-green-600" : "bg-blue-600"
        }`}
      >
        {method}
      </span>
      <code className="text-sm font-mono text-dark dark:text-light">{path}</code>
    </div>
    <div className="px-6 py-4">
      <p className="text-dark/80 dark:text-light/80 mb-4">{description}</p>
      {children}
    </div>
  </motion.div>
);

const RateLimitRow = ({ tier, requests, price, features }) => (
  <tr className="border-b border-dark/10 dark:border-light/10">
    <td className="px-4 py-3 font-semibold text-dark dark:text-light">{tier}</td>
    <td className="px-4 py-3 text-dark/80 dark:text-light/80">{requests}</td>
    <td className="px-4 py-3 text-dark/80 dark:text-light/80">{price}</td>
    <td className="px-4 py-3 text-dark/70 dark:text-light/70 text-sm">{features}</td>
  </tr>
);

export default function ApiAccess() {
  return (
    <>
      <Head>
        <title>API Documentation | Partition Framework</title>
        <meta
          name="description"
          content="REST API for cell state instantiation, disease detection, and drug design using the partition framework."
        />
      </Head>

      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="API Documentation"
            className="mb-16 !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
          />

          {/* Overview */}
          <Section title="Overview" id="overview">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The Partition Framework API provides programmatic access to the
              cell state instantiation engine, disease detection module, and
              drug design tools. The API accepts partial cellular observations
              and returns complete, validated cell states using the purpose-partitioned
              compilation pipeline.
            </p>
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              All API endpoints return JSON responses and accept JSON request bodies.
              The base URL for all endpoints is:
            </p>
            <CodeBlock>https://api.partition-framework.org/v1</CodeBlock>
          </Section>

          {/* Authentication */}
          <Section title="Authentication" id="authentication">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              All API requests require authentication via an API key passed in the
              request header. API keys can be generated from the dashboard after
              creating an account.
            </p>
            <CodeBlock title="Authentication Header">
{`Authorization: Bearer YOUR_API_KEY
Content-Type: application/json`}
            </CodeBlock>
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Unauthenticated requests will receive a 401 response. Invalid or expired
              API keys will receive a 403 response with a descriptive error message.
            </p>
          </Section>

          {/* Endpoints */}
          <Section title="Endpoints" id="endpoints">
            {/* POST /instantiate */}
            <EndpointCard
              method="POST"
              path="/api/v1/instantiate"
              description="Submit partial cellular observations and receive a complete, validated cell state through the four-stage compilation pipeline (observe → catalyze → fuse → access)."
            >
              <CodeBlock title="Request Body">
{`{
  "organism": "e_coli",
  "observations": {
    "metabolites": {
      "glucose": 5.0,
      "g6p": 0.083,
      "atp": 1.8
    },
    "fluxes": {
      "hexokinase": 0.1
    },
    "confidence": 0.95
  },
  "options": {
    "pipeline_stages": ["observe", "catalyze", "fuse", "access"],
    "return_intermediates": false,
    "fuzzy_alpha": 0.9
  }
}`}
              </CodeBlock>
              <CodeBlock title="Response (200 OK)">
{`{
  "status": "success",
  "cell_state": {
    "metabolites": {
      "glucose": 5.001,
      "g6p": 0.083,
      "f6p": 0.014,
      "fbp": 0.032,
      "gap": 0.015,
      "bpg": 0.001,
      "3pg": 0.100,
      "2pg": 0.017,
      "pep": 0.023,
      "pyruvate": 0.051,
      "atp": 1.800,
      "adp": 0.200,
      "nad": 0.500,
      "nadh": 0.050
    },
    "fluxes": {
      "hexokinase": 0.100,
      "pgi": 0.100,
      "pfk": 0.100,
      "aldolase": 0.100,
      "tpi": 0.100,
      "gapdh": 0.100,
      "pgk": 0.100,
      "pgm": 0.100,
      "enolase": 0.100,
      "pyruvate_kinase": 0.100
    },
    "categorical_address": [1.99, 5.58, 8.15, 7.00, 7.71, 11.96, 5.05, 7.05, 7.43, 6.28],
    "coherence": 1.0,
    "mare": 0.0001
  },
  "pipeline_report": {
    "observe_mare": 2.67,
    "catalyze_mare": 0.94,
    "fuse_mare": 0.23,
    "access_mare": 0.0001,
    "total_time_ms": 142
  }
}`}
              </CodeBlock>
            </EndpointCard>

            {/* POST /diagnose */}
            <EndpointCard
              method="POST"
              path="/api/v1/diagnose"
              description="Submit a cell state (complete or partial) and receive a disease assessment. The system computes the categorical address, compares to the healthy trajectory manifold, and identifies any enzyme deficiencies."
            >
              <CodeBlock title="Request Body">
{`{
  "organism": "human",
  "cell_state": {
    "metabolites": {
      "glucose": 8.5,
      "g6p": 0.002,
      "f6p": 0.001,
      "pyruvate": 0.005
    }
  }
}`}
              </CodeBlock>
              <CodeBlock title="Response (200 OK)">
{`{
  "status": "success",
  "diagnosis": {
    "is_healthy": false,
    "coherence": 0.0,
    "detected_deficiencies": [
      {
        "enzyme": "hexokinase",
        "confidence": 0.98,
        "escape_direction": [0.92, -0.38, 0.04],
        "severity": "complete_knockout"
      }
    ],
    "trajectory_deviation": 4.72,
    "threshold": 0.5,
    "recommendation": "Hexokinase deficiency detected with 98% confidence. Consistent with Type 1 HK deficiency pattern."
  }
}`}
              </CodeBlock>
            </EndpointCard>

            {/* POST /drug-design */}
            <EndpointCard
              method="POST"
              path="/api/v1/drug-design"
              description="Submit a disease state and receive suggested conductance modifications (drug targets) that would restore the cell to the healthy trajectory manifold."
            >
              <CodeBlock title="Request Body">
{`{
  "organism": "human",
  "disease_state": {
    "deficiency": "hexokinase",
    "severity": "partial",
    "residual_activity": 0.15
  },
  "constraints": {
    "max_targets": 3,
    "avoid_enzymes": ["pfk"],
    "target_coherence": 0.95
  }
}`}
              </CodeBlock>
              <CodeBlock title="Response (200 OK)">
{`{
  "status": "success",
  "drug_design": {
    "targets": [
      {
        "enzyme": "glucokinase",
        "modification": "activation",
        "required_fold_change": 2.4,
        "mechanism": "allosteric_activator",
        "predicted_coherence": 0.97
      },
      {
        "enzyme": "glucose_transporter",
        "modification": "upregulation",
        "required_fold_change": 1.8,
        "mechanism": "transcriptional_activation",
        "predicted_coherence": 0.93
      }
    ],
    "combined_coherence": 0.99,
    "closure_restored": true
  }
}`}
              </CodeBlock>
            </EndpointCard>

            {/* GET /catalysts */}
            <EndpointCard
              method="GET"
              path="/api/v1/catalysts"
              description="List all available biological catalysts in the vocabulary, including their types, exclusion factors, and resolution contributions."
            >
              <CodeBlock title="Response (200 OK)">
{`{
  "status": "success",
  "catalysts": [
    {
      "id": 1,
      "name": "Kinase",
      "type": "phosphorylation",
      "exclusion_factor": 0.42,
      "resolution_nm": 116.0
    },
    {
      "id": 2,
      "name": "Phosphatase",
      "type": "dephosphorylation",
      "exclusion_factor": 0.38,
      "resolution_nm": 71.9
    }
  ],
  "total": 12
}`}
              </CodeBlock>
            </EndpointCard>

            {/* GET /network */}
            <EndpointCard
              method="GET"
              path="/api/v1/network/{organism}"
              description="Retrieve the metabolic network graph for a specified organism. Returns nodes (metabolites), edges (reactions), and their associated categorical properties."
            >
              <CodeBlock title="Example: GET /api/v1/network/e_coli">
{`{
  "status": "success",
  "organism": "e_coli",
  "network": {
    "nodes": 1136,
    "edges": 2251,
    "subsystems": 92,
    "sample_node": {
      "id": "glc_D",
      "name": "D-Glucose",
      "categorical_depth": 1.99,
      "compartment": "cytoplasm"
    },
    "sample_edge": {
      "id": "HEX1",
      "name": "Hexokinase",
      "substrates": ["glc_D", "atp"],
      "products": ["g6p", "adp"],
      "flux_bounds": [-1000, 1000]
    }
  }
}`}
              </CodeBlock>
            </EndpointCard>
          </Section>

          {/* Rate Limits */}
          <Section title="Rate Limits" id="rate-limits">
            <p className="text-dark/80 dark:text-light/80 mb-6 leading-relaxed">
              API rate limits depend on your subscription tier. Exceeding the rate limit
              returns a 429 response with a Retry-After header.
            </p>

            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-dark dark:text-light">
                <thead>
                  <tr className="border-b-2 border-dark/20 dark:border-light/20">
                    <th className="px-4 py-3 text-left font-semibold">Tier</th>
                    <th className="px-4 py-3 text-left font-semibold">Requests/Day</th>
                    <th className="px-4 py-3 text-left font-semibold">Price</th>
                    <th className="px-4 py-3 text-left font-semibold">Features</th>
                  </tr>
                </thead>
                <tbody>
                  <RateLimitRow
                    tier="Academic (Free)"
                    requests="100"
                    price="Free"
                    features="Basic instantiation, single organism"
                  />
                  <RateLimitRow
                    tier="Professional"
                    requests="10,000"
                    price="$299/mo"
                    features="Full API, all organisms, disease detection, drug design"
                  />
                  <RateLimitRow
                    tier="Enterprise"
                    requests="Unlimited"
                    price="Custom"
                    features="All features + custom models + on-premise deployment"
                  />
                </tbody>
              </table>
            </div>
          </Section>

          {/* Error Codes */}
          <Section title="Error Handling" id="errors">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The API uses standard HTTP status codes and returns descriptive error
              messages in JSON format.
            </p>

            <CodeBlock title="Error Response Format">
{`{
  "status": "error",
  "code": 422,
  "message": "Invalid organism identifier",
  "details": {
    "field": "organism",
    "value": "unknown_species",
    "allowed": ["e_coli", "s_cerevisiae", "h_sapiens"]
  }
}`}
            </CodeBlock>

            <div className="overflow-x-auto mt-6">
              <table className="min-w-full text-sm text-dark dark:text-light">
                <thead>
                  <tr className="border-b-2 border-dark/20 dark:border-light/20">
                    <th className="px-4 py-3 text-left font-semibold">Code</th>
                    <th className="px-4 py-3 text-left font-semibold">Meaning</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark/10 dark:divide-light/10">
                  <tr>
                    <td className="px-4 py-2 font-mono">200</td>
                    <td className="px-4 py-2">Success</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">400</td>
                    <td className="px-4 py-2">Bad request (malformed JSON, missing required fields)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">401</td>
                    <td className="px-4 py-2">Unauthorized (missing API key)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">403</td>
                    <td className="px-4 py-2">Forbidden (invalid API key or insufficient permissions)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">422</td>
                    <td className="px-4 py-2">Unprocessable entity (valid JSON but invalid parameters)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">429</td>
                    <td className="px-4 py-2">Rate limit exceeded</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">500</td>
                    <td className="px-4 py-2">Internal server error</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Section>

          {/* SDKs */}
          <Section title="SDK Support" id="sdks">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Official SDKs are available for Python, R, and JavaScript/TypeScript.
              Community SDKs are available for Julia, MATLAB, and Go.
            </p>

            <CodeBlock title="Python SDK Example">
{`from partition_framework import PartitionClient

client = PartitionClient(api_key="your_key")

# Instantiate a cell state from partial observations
state = client.instantiate(
    organism="e_coli",
    metabolites={"glucose": 5.0, "atp": 1.8},
    confidence=0.95
)

print(f"Coherence: {state.coherence}")
print(f"MARE: {state.mare}")
print(f"Pyruvate: {state.metabolites['pyruvate']}")

# Diagnose
diagnosis = client.diagnose(state)
if not diagnosis.is_healthy:
    print(f"Deficiency: {diagnosis.detected_deficiencies[0].enzyme}")
`}
            </CodeBlock>

            <CodeBlock title="R SDK Example">
{`library(partitionframework)

client <- pf_connect(api_key = "your_key")

# Get metabolic network
network <- pf_network(client, organism = "s_cerevisiae")

# Instantiate with flux measurements
state <- pf_instantiate(client,
  organism = "s_cerevisiae",
  fluxes = list(hexokinase = 0.1, pfk = 0.1),
  fuzzy_alpha = 0.9
)

# Plot categorical address
plot(state$categorical_address, type = "h",
     main = "Categorical Depth Profile")
`}
            </CodeBlock>
          </Section>
        </Layout>
      </main>
    </>
  );
}
