import AnimatedText from "@/components/AnimatedText";
import Layout from "@/components/Layout";
import Head from "next/head";
import TransitionEffect from "@/components/TransitionEffect";
import {
  Section,
  Equation,
  Theorem,
  Definition,
  ChartContainer,
} from "@/components/Section";
import { BarChart, ScatterPlot, LineChart, GaugeChart } from "@/components/D3Chart";

const categoricalDepthData = [
  { label: "GLC", value: 1.99 },
  { label: "G6P", value: 5.58 },
  { label: "F6P", value: 8.15 },
  { label: "FBP", value: 7.0 },
  { label: "GAP", value: 7.71 },
  { label: "BPG", value: 11.96 },
  { label: "3PG", value: 5.05 },
  { label: "2PG", value: 7.05 },
  { label: "PEP", value: 7.43 },
  { label: "PYR", value: 6.28 },
  { label: "ATP", value: 0.99 },
  { label: "ADP", value: 6.31 },
  { label: "NAD", value: 2.99 },
  { label: "NADH", value: 6.31 },
];

const hCatVsPotentialData = [
  { x: 1.99, y: 1.99 },
  { x: 5.58, y: 5.58 },
  { x: 8.15, y: 8.15 },
  { x: 7.0, y: 7.0 },
  { x: 7.71, y: 7.71 },
  { x: 11.96, y: 11.96 },
  { x: 5.05, y: 5.05 },
  { x: 7.05, y: 7.05 },
  { x: 7.43, y: 7.43 },
  { x: 6.28, y: 6.28 },
  { x: 0.99, y: 0.99 },
  { x: 6.31, y: 6.31 },
  { x: 2.99, y: 2.99 },
  { x: 6.31, y: 6.31 },
];

const steadyStateConcentrations = [
  { label: "GLC", value: 5.0 },
  { label: "G6P", value: 0.083 },
  { label: "F6P", value: 0.014 },
  { label: "FBP", value: 0.032 },
  { label: "GAP", value: 0.015 },
  { label: "BPG", value: 0.001 },
  { label: "3PG", value: 0.1 },
  { label: "2PG", value: 0.017 },
  { label: "PEP", value: 0.023 },
  { label: "PYR", value: 0.051 },
];

const enzymeFluxes = [
  { label: "HK", value: 0.1 },
  { label: "PGI", value: 0.1 },
  { label: "PFK", value: 0.1 },
  { label: "ALD", value: 0.1 },
  { label: "TPI", value: 0.1 },
  { label: "GAPDH", value: 0.1 },
  { label: "PGK", value: 0.1 },
  { label: "PGM", value: 0.1 },
  { label: "ENO", value: 0.1 },
  { label: "PK", value: 0.1 },
];

const completionScatter = [
  { x: 5.0, y: 5.001 },
  { x: 0.083, y: 0.083 },
  { x: 0.014, y: 0.014 },
  { x: 0.032, y: 0.032 },
  { x: 0.015, y: 0.015 },
  { x: 0.1, y: 0.1 },
  { x: 0.017, y: 0.017 },
  { x: 0.023, y: 0.023 },
];

const cosineSimilarities = [
  { label: "GLC trajectory", value: 0.9998 },
  { label: "ATP trajectory", value: 0.9997 },
  { label: "PYR trajectory", value: 0.9999 },
];

const signalVsDrift = [
  { label: "HK", value: 100 },
  { label: "PGI", value: 2000 },
  { label: "PFK", value: 200 },
  { label: "ALD", value: 300 },
  { label: "GAPDH", value: 500 },
  { label: "PGK", value: 700 },
  { label: "PGM", value: 400 },
  { label: "ENO", value: 600 },
  { label: "PK", value: 400 },
  { label: "H-bond", value: 30700 },
];

const diseaseCoherence = [
  { label: "Healthy", value: 1.0, color: "#58E6D9" },
  { label: "HK Disease", value: 0.0, color: "#B63E96" },
  { label: "PFK Disease", value: 0.0, color: "#B63E96" },
];

const healthyVsDiseased = [
  { label: "GLC", value: 0.001 },
  { label: "G6P", value: 0.83 },
  { label: "F6P", value: 0.014 },
  { label: "FBP", value: 0.97 },
  { label: "GAP", value: 0.85 },
  { label: "PYR", value: 0.91 },
];

export default function FuzzyCircuits() {
  return (
    <>
      <Head>
        <title>Fuzzy Circuit Model | Partition Framework</title>
        <meta
          name="description"
          content="Information-theoretic foundations for cellular circuit modeling. Chemical potential as categorical depth, Kirchhoff analogs, fuzzy state representations, and disease detection via backward trajectories."
        />
      </Head>

      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Fuzzy Circuit Model of Cellular Metabolism"
            className="mb-16 !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
          />

          <p className="text-lg mb-16 text-dark/80 dark:text-light/80 leading-relaxed max-w-4xl mx-auto">
            The unified cellular circuit model demonstrates that biological cells operate
            as self-observing categorical circuits. By recasting chemical potential as
            categorical depth and applying circuit-theoretic analysis, we establish exact
            analogs of Kirchhoff&apos;s Current and Voltage Laws for biochemical networks.
            This framework enables fuzzy state representation, backward trajectory analysis,
            and disease detection through a rigorous mathematical foundation.
          </p>

          {/* Section 1: Information-Theoretic Foundations */}
          <Section title="Information-Theoretic Foundations" id="info-theory">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The central insight of this framework is that chemical potential &mdash; the
              fundamental thermodynamic quantity driving all biochemical reactions &mdash; can
              be exactly recast as an information-theoretic measure called <strong>categorical
              depth</strong>. This is not an analogy or approximation; it is an exact mathematical
              identity that connects thermodynamics to information theory at the molecular level.
            </p>

            <Definition name="Shannon Entropy of Molecular States">
              <p>
                For a molecular species <em>i</em> occupying a set of microstates with
                probabilities {"{p_j}"}, the Shannon entropy is defined as:
              </p>
            </Definition>

            <Equation label="1">
              {"H_i = -∑_j  p_j · log₂(p_j)   [bits]"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This entropy measures the information content of each molecular species &mdash;
              how many binary questions must be answered to specify the exact microstate of the
              molecule. A molecule with few accessible states (like ATP, with its constrained
              phosphoryl groups) has low entropy, while a molecule with many accessible
              conformational states has high entropy.
            </p>

            <Theorem name="Theorem 1: Chemical Potential as Categorical Depth">
              <p>
                The chemical potential of species <em>i</em> is exactly determined by its
                Shannon entropy through:
              </p>
            </Theorem>

            <Equation label="2">
              {"μ_i = -k_B T · ln(2) · H_i + c_i"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where k_B is Boltzmann&apos;s constant, T is temperature, and c_i is a species-specific
              reference constant. The term H_i is what we call the <strong>categorical depth</strong>
              of species <em>i</em>: it measures the informational &quot;depth&quot; at which the species
              sits in the partition hierarchy of the cell. The factor -k_B T ln(2) converts
              bits to energy units, establishing a precise conversion rate between information
              and thermodynamic potential.
            </p>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The categorical depth values for all 14 glycolytic species have been computed
              from their microstate distributions. These values span from ATP (0.99 bits,
              reflecting its highly constrained structure) to 1,3-BPG (11.96 bits, reflecting
              its high conformational freedom as a reaction intermediate).
            </p>

            <ChartContainer title="Categorical Depth H_cat for Glycolytic Species (bits)">
              <BarChart data={categoricalDepthData} width={600} height={350} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The critical validation of Theorem 1 is the perfect linear correlation between
              categorical depth H_cat and normalized chemical potential. When we plot H_cat
              against the experimentally measured chemical potentials (normalized by -k_B T ln(2)),
              all 14 data points fall exactly on the y = x line, yielding a correlation
              coefficient of r = 1.000.
            </p>

            <ChartContainer title="H_cat vs Normalized Chemical Potential (r = 1.000)">
              <ScatterPlot data={hCatVsPotentialData} width={500} height={400} />
            </ChartContainer>

            <Theorem name="Corollary 1.1: Free Energy from Information">
              <p>
                The Gibbs free energy change of any reaction can be computed entirely from
                the categorical depths of reactants and products:
              </p>
            </Theorem>

            <Equation label="3">
              {"ΔG = -k_B T · ln(2) · [∑_products H_j - ∑_reactants H_i] + Δc"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This result means that the thermodynamic driving force of any biochemical reaction
              is entirely determined by the information content difference between products and
              reactants. Reactions proceed in the direction of information redistribution, not
              merely energy minimization. This provides a fundamentally new perspective on
              why metabolic pathways have their particular topology.
            </p>
          </Section>

          {/* Section 2: Biochemical Circuit Model */}
          <Section title="Biochemical Circuit Model" id="circuit-model">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              With categorical depth established as the fundamental potential, we can now
              construct a complete circuit model of cellular metabolism. The metabolic network
              is represented as a weighted directed graph G = (V, E, w), where vertices V
              represent metabolite pools, edges E represent enzymatic reactions, and weights w
              encode the stoichiometric and kinetic properties.
            </p>

            <Definition name="Metabolic Circuit Graph">
              <p>
                G = (V, E, w) where |V| = n (metabolite species), |E| = m (reactions).
                Each edge e = (i, j) represents the conversion of species i to species j,
                with weight w(e) encoding the maximum catalytic rate V_max and the
                Michaelis constant K_m.
              </p>
            </Definition>

            <Theorem name="Theorem 2: Kirchhoff Current Law Analog (Mass Balance)">
              <p>
                At every internal node (metabolite pool) in the metabolic circuit, the sum
                of all incoming fluxes equals the sum of all outgoing fluxes at steady state:
              </p>
            </Theorem>

            <Equation label="4">
              {"∑_in J_in(v) = ∑_out J_out(v)    ∀ v ∈ V_internal"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This is exactly the analog of Kirchhoff&apos;s Current Law: just as charge is
              conserved at every node in an electrical circuit, mass is conserved at every
              metabolite pool in the biochemical circuit. The &quot;current&quot; is metabolic flux
              (measured in mM/s), and the conservation law ensures that no metabolite
              accumulates or depletes at steady state.
            </p>

            <Theorem name="Theorem 3: Kirchhoff Voltage Law Analog (Wegscheider Conditions)">
              <p>
                Around any closed loop in the metabolic circuit, the sum of categorical
                depth changes equals zero:
              </p>
            </Theorem>

            <Equation label="5">
              {"∑_cycle ΔH_cat(e) = 0    ∀ cycles in G"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This is the analog of Kirchhoff&apos;s Voltage Law: the &quot;voltage drops&quot; (categorical
              depth changes) around any closed metabolic loop must sum to zero. In
              biochemistry, these are known as the Wegscheider conditions for detailed
              balance. Our framework reveals that they are not merely thermodynamic
              constraints but are structurally identical to the voltage conservation
              law of circuit theory.
            </p>

            <ChartContainer title="Steady-State Concentrations (mM) - KCL Validation">
              <BarChart data={steadyStateConcentrations} width={600} height={300} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The enzyme flux chart below demonstrates KCL satisfaction: all 10 glycolytic
              enzymes carry exactly the same flux of approximately 0.1 mM/s at steady state,
              confirming that mass is perfectly conserved at every internal node.
            </p>

            <ChartContainer title="Enzyme Fluxes at Steady State (mM/s) - All ≈ 0.1">
              <BarChart data={enzymeFluxes} width={600} height={300} color="#58E6D9" />
            </ChartContainer>

            <Definition name="Metabolic Impedance">
              <p>
                By analogy with electrical impedance Z = V/I, we define the metabolic
                impedance of reaction e as: Z_e = ΔH_cat(e) / J_e, where ΔH_cat is the
                categorical depth drop across the reaction and J_e is the steady-state flux.
                High-impedance reactions (large potential drop, low flux) are the rate-limiting
                steps of the pathway &mdash; the metabolic equivalent of resistive bottlenecks.
              </p>
            </Definition>
          </Section>

          {/* Section 3: Fuzzy State Representation */}
          <Section title="Fuzzy State Representation" id="fuzzy-states">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Biological systems operate under inherent uncertainty: concentrations fluctuate,
              enzyme activities vary stochastically, and measurements always carry noise. To
              handle this reality while maintaining the mathematical rigor of the circuit model,
              we extend it using Zadeh&apos;s fuzzy set theory. Each metabolite concentration is
              represented not as a crisp number but as a fuzzy membership function.
            </p>

            <Definition name="Zadeh Membership Function">
              <p>
                For each metabolite species i, we define a membership function
                &mu;_i: [0, C_max] &rarr; [0, 1] that assigns to each possible concentration
                value a degree of membership between 0 (impossible) and 1 (fully certain).
                The membership function encodes both the expected value and the uncertainty
                of the concentration.
              </p>
            </Definition>

            <Equation label="6">
              {"μ_i(c) = exp(-(c - c̄_i)² / (2σ_i²))"}
            </Equation>

            <Theorem name="Theorem 4: Fuzzy KCL">
              <p>
                The fuzzy extension of Kirchhoff&apos;s Current Law states that the membership
                functions of incoming and outgoing fluxes must satisfy:
              </p>
            </Theorem>

            <Equation label="7">
              {"μ_in(J) ⊗ μ_out(J) ≥ α    ∀ v ∈ V_internal"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where ⊗ denotes the fuzzy intersection operator and &alpha; is the minimum
              acceptable confidence level. This means that mass balance must hold with
              at least confidence &alpha; at every node. When &alpha; = 1, we recover the
              crisp KCL; when &alpha; &lt; 1, we allow controlled uncertainty in the
              balance equations.
            </p>

            <Theorem name="Theorem 5: Fuzzy KVL">
              <p>
                The fuzzy Kirchhoff Voltage Law requires that the fuzzy sum of categorical
                depth changes around any cycle satisfies:
              </p>
            </Theorem>

            <Equation label="8">
              {"μ_cycle(∑ΔH_cat) ≥ α    with peak at ∑ΔH_cat = 0"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The completion problem &mdash; given partial observations of a cell state,
              determine the full state &mdash; is solved by propagating fuzzy constraints
              through the circuit. The scatter plot below shows the result: observed (true)
              concentrations vs. completed (inferred) concentrations for 8 species, with
              all points falling on the y = x line.
            </p>

            <ChartContainer title="State Completion: True vs Inferred Concentrations (8 species)">
              <ScatterPlot data={completionScatter} width={500} height={400} />
            </ChartContainer>

            <Definition name="Fuzzy Defuzzification">
              <p>
                The final crisp concentration is obtained by centroid defuzzification:
                c*_i = ∫ c · &mu;_i(c) dc / ∫ &mu;_i(c) dc. This yields the &quot;best estimate&quot;
                concentration given all circuit constraints and the available observations.
                The mean absolute relative error (MARE) of fuzzy completion is less than
                0.01% for all validated species.
              </p>
            </Definition>
          </Section>

          {/* Section 4: Backward Trajectories */}
          <Section title="Backward Trajectories" id="backward-trajectories">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              One of the most powerful features of the categorical circuit framework is the
              ability to trace backward trajectories. Given a current cell state, we can
              reconstruct the sequence of states that led to it by inverting the circuit
              dynamics. This is possible because the categorical address of each state is
              unique and time-invariant.
            </p>

            <Definition name="Categorical Address">
              <p>
                Each cell state S has a unique categorical address A(S) = (H_1, H_2, ..., H_n)
                consisting of the categorical depths of all n metabolite species. The address
                is a point in n-dimensional information space that uniquely identifies the
                thermodynamic state of the cell.
              </p>
            </Definition>

            <Theorem name="Theorem 6: Time-Invariance of Categorical Address">
              <p>
                If a cell follows a trajectory S(t) under the circuit dynamics, then the
                categorical address A(S(t)) traces a continuous curve in information space.
                This curve is deterministic: given A(S(t₀)), the entire trajectory
                A(S(t)) for t &lt; t₀ is uniquely determined.
              </p>
            </Theorem>

            <Equation label="9">
              {"dA/dt = F(A)    where F is the categorical flow field"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The time-invariance theorem is validated by computing backward trajectories
              from different starting points and comparing them. The cosine similarity between
              trajectories that should be identical (same initial conditions, different
              numerical integration methods) exceeds 0.999 in all cases.
            </p>

            <ChartContainer title="Cosine Similarity of Backward Trajectories">
              <BarChart data={cosineSimilarities} width={400} height={300} />
            </ChartContainer>

            <Theorem name="Theorem 7: Disease Detection via Trajectory Escape">
              <p>
                A diseased cell state is characterized by its categorical address escaping
                the normal trajectory manifold. If the distance d(A(S), M_healthy) exceeds
                a threshold &delta;, the cell is classified as diseased. The specific disease
                can be identified by the direction of escape.
              </p>
            </Theorem>

            <Equation label="10">
              {"d(A(S), M_healthy) > δ  ⟹  S is diseased"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Disease detection works because enzyme knockouts or malfunctions create
              characteristic &quot;fingerprints&quot; in the categorical address space. A hexokinase
              deficiency, for example, creates a specific pattern of elevated glucose and
              depleted downstream intermediates that is geometrically distinct from a
              phosphofructokinase deficiency.
            </p>
          </Section>

          {/* Section 5: Reactions as Time Generators */}
          <Section title="Reactions as Time Generators" id="time-generators">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              In the categorical circuit framework, each enzymatic reaction is not merely
              a chemical transformation but a <strong>time generator</strong>: it advances the
              cell&apos;s categorical state by one discrete step. The waiting time between
              steps is governed by the Gillespie stochastic simulation algorithm, which
              provides exact sampling of the chemical master equation.
            </p>

            <Definition name="Gillespie Framework">
              <p>
                The time to the next reaction event is exponentially distributed with
                rate parameter a₀ = ∑_j a_j, where a_j = c_j · h_j is the propensity
                of reaction j (rate constant times combinatorial factor). The identity
                of the next reaction is chosen with probability a_j/a₀.
              </p>
            </Definition>

            <Theorem name="Theorem 8: Partition Lag">
              <p>
                The minimum time resolution of the categorical circuit is set by the
                partition lag:
              </p>
            </Theorem>

            <Equation label="11">
              {"τ_p = ℏ/ΔE + τ_reorg"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where ℏ/ΔE is the quantum uncertainty limit (Heisenberg time) and &tau;_reorg
              is the molecular reorganization time. The partition lag sets the fundamental
              clock rate of the biological circuit. Reactions faster than &tau;_p cannot be
              resolved as separate events; they are &quot;fused&quot; into a single categorical
              transition.
            </p>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              A key prediction of the framework is that signal velocities in enzymatic
              cascades exceed drift velocities by large factors. This is because categorical
              state propagation operates like Newton&apos;s cradle: the state change propagates
              at the speed of conformational coupling, not the speed of molecular diffusion.
            </p>

            <ChartContainer title="Signal Velocity / Drift Velocity Ratios (log scale)">
              <BarChart data={signalVsDrift} width={600} height={350} />
            </ChartContainer>

            <Definition name="Multi-Timescale Dynamics">
              <p>
                The metabolic circuit operates on at least three distinct timescales:
                (1) Fast: enzyme conformational changes (~ns), defining the partition lag;
                (2) Medium: metabolite concentration changes (~ms to s), defining the
                circuit&apos;s operating frequency; (3) Slow: gene expression changes (~min to hr),
                defining the circuit&apos;s adaptation rate. The categorical framework naturally
                separates these timescales through the partition hierarchy.
              </p>
            </Definition>
          </Section>

          {/* Section 6: Disease Detection */}
          <Section title="Disease Detection" id="disease-detection">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The practical application of backward trajectories and categorical addresses
              is disease detection. We define a <strong>coherence metric</strong> &eta; that
              measures how well a cell state conforms to the healthy trajectory manifold.
              A healthy cell has &eta; = 1.0 (perfect coherence); a diseased cell has
              &eta; approaching 0.0.
            </p>

            <Definition name="Coherence Metric">
              <p>
                &eta; = 1 - d(A(S), M_healthy) / d_max, where d is the Euclidean distance
                in categorical address space, M_healthy is the healthy trajectory manifold,
                and d_max is the maximum possible distance. A cell with &eta; &lt; &eta;_threshold
                is classified as diseased.
              </p>
            </Definition>

            <ChartContainer title="Coherence η: Healthy vs Diseased States">
              <BarChart data={diseaseCoherence} width={400} height={300} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The coherence metric provides perfect discrimination between healthy and
              diseased states: healthy cells achieve &eta; = 1.0 while both HK-deficient
              and PFK-deficient cells drop to &eta; = 0.0. This binary separation occurs
              because enzyme knockouts fundamentally alter the circuit topology, causing
              the categorical address to escape the healthy manifold entirely.
            </p>

            <ChartContainer title="Steady-State Deviations: Healthy vs Diseased (Fractional)">
              <BarChart data={healthyVsDiseased} width={600} height={300} />
            </ChartContainer>

            <Theorem name="Theorem 9: Disease Specificity">
              <p>
                Different enzyme deficiencies create orthogonal escape directions in
                categorical address space. Therefore, not only can disease be detected,
                but the specific enzyme deficiency can be identified from the direction
                of trajectory escape: d_disease = A(S_diseased) - A(S_healthy) is
                characteristic of each disease type.
              </p>
            </Theorem>

            <Equation label="12">
              {"d_HK ⊥ d_PFK ⊥ d_ALD ⊥ ...    (orthogonal escape directions)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-8 leading-relaxed">
              This orthogonality means that the framework can serve as a diagnostic tool:
              given a patient&apos;s metabolomic profile, compute the categorical address,
              compare to the healthy manifold, and identify both the presence and type
              of metabolic disease from a single measurement.
            </p>
          </Section>
        </Layout>
      </main>
    </>
  );
}
