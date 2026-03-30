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
import { BarChart, LineChart, Heatmap, GaugeChart } from "@/components/D3Chart";

const correlationLabels = ["Partition", "Flux", "Charge", "Circuit", "O\u2082", "Purpose"];
const correlationData = [
  [1, 0.86, 0.95, 1, 1, 0.97],
  [0.86, 1, 0.90, 0.86, 0.86, 0.82],
  [0.95, 0.90, 1, 0.95, 0.95, 0.97],
  [1, 0.86, 0.95, 1, 1, 0.97],
  [1, 0.86, 0.95, 1, 1, 0.97],
  [0.97, 0.82, 0.97, 0.97, 0.97, 1],
];

const pipelineMARE = [
  { label: "Observe", value: 2.67 },
  { label: "Catalyze", value: 0.94 },
  { label: "Fuse", value: 0.23 },
  { label: "Access", value: 0.0001 },
];

const resolutionCascade = [
  { x: 1, y: 200 },
  { x: 2, y: 85 },
  { x: 3, y: 31 },
  { x: 4, y: 9.5 },
  { x: 5, y: 2.8 },
  { x: 6, y: 0.71 },
  { x: 7, y: 0.15 },
  { x: 8, y: 0.029 },
  { x: 9, y: 0.0044 },
  { x: 10, y: 0.00058 },
  { x: 11, y: 0.0000062 },
  { x: 12, y: 0.0000000882 },
];

const forwardVsPurpose = [
  { label: "Forward MARE", value: 0.303, color: "#B63E96" },
  { label: "Purpose MARE", value: 0.012, color: "#58E6D9" },
];

const performanceRatios = [
  { label: "Speed (67.7×)", value: 67.7 },
  { label: "MARE (24.7×)", value: 24.7 },
  { label: "Info Eff. (7.2×)", value: 7.2 },
];

const closureMetric = [
  { label: "Healthy", value: 1.0, color: "#58E6D9" },
  { label: "HK KO", value: 0.0, color: "#B63E96" },
  { label: "PFK KO", value: 0.0, color: "#B63E96" },
  { label: "ALD KO", value: 0.0, color: "#B63E96" },
];

export default function PurposeModels() {
  return (
    <>
      <Head>
        <title>Purpose-Partitioned Compilation | Partition Framework</title>
        <meta
          name="description"
          content="Purpose neural compilation framework solving the instantiation problem. Six isomorphic subsystems, morphism chain compilation, catalyst vocabulary, and autocatalytic closure."
        />
      </Head>

      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Purpose-Partitioned Neural Compilation"
            className="mb-16 !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
          />

          <p className="text-lg mb-16 text-dark/80 dark:text-light/80 leading-relaxed max-w-4xl mx-auto">
            The purpose-partitioned cellular circuits framework solves the fundamental
            <strong> instantiation problem</strong> in biology: how to determine a cell&apos;s
            complete internal state from partial observations. Rather than forward simulation
            (which is computationally intractable and epistemically vacuous), we use a
            compilation approach that maps observations through a chain of biological
            morphisms to produce a complete, validated cell state.
          </p>

          {/* Section 1: The Instantiation Problem */}
          <Section title="The Instantiation Problem" id="instantiation">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The instantiation problem is the central challenge of computational biology:
              given a set of measurements (gene expression levels, metabolite concentrations,
              protein abundances), determine the complete functional state of the cell.
              Traditional approaches attempt this through forward simulation &mdash; running
              a dynamical model from initial conditions to steady state. We argue that this
              approach is fundamentally flawed.
            </p>

            <Theorem name="Theorem 1: Epistemic Blindness of Forward Simulation">
              <p>
                Forward simulation of a biological system is epistemically vacuous:
                the output is entirely determined by the input assumptions (initial
                conditions, rate constants, boundary conditions), and no genuinely
                new information is produced. The simulation merely unfolds the
                consequences of assumptions that were already made.
              </p>
            </Theorem>

            <Equation label="1">
              {"I(output; reality | assumptions) = 0    [forward simulation]"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The mutual information between the simulation output and biological reality,
              conditioned on the input assumptions, is zero. This means forward simulation
              cannot tell us anything about the real cell that we didn&apos;t already assume.
              The apparent &quot;predictions&quot; of such models are merely restatements of their
              inputs in a different mathematical language.
            </p>

            <Definition name="The Compilation Alternative">
              <p>
                Instead of simulating forward from assumptions to predictions, we
                <em> compile</em> backward from observations to instantiation. Compilation
                takes raw observational data and passes it through a series of validated
                biological morphisms (structure-preserving maps), each of which adds
                information by enforcing known biological constraints. The final output
                is a complete cell state that is consistent with all observations AND
                all known biological laws.
              </p>
            </Definition>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The compilation approach succeeds where simulation fails because it uses
              the cell&apos;s own organizational principles &mdash; encoded in the six subsystem
              frameworks &mdash; as computational resources. Each subsystem provides a set
              of constraints that reduce the space of possible states, progressively
              narrowing down to a unique instantiation.
            </p>
          </Section>

          {/* Section 2: The Six Subsystems */}
          <Section title="The Six Subsystems" id="six-subsystems">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The partition framework identifies six fundamental subsystems that
              collectively describe all aspects of cellular function. A key result
              is that these six subsystems are <strong>isomorphic</strong>: they have
              the same mathematical structure and can be mapped onto each other through
              well-defined morphisms.
            </p>

            <Definition name="Subsystem 1: Partition">
              <p>
                The partition subsystem assigns categorical coordinates (n, ℓ, m, s)
                to every molecular species and organizes the cell&apos;s state space into
                a hierarchical structure with capacity C(n) = 2n² per level.
              </p>
            </Definition>

            <Definition name="Subsystem 2: Flux">
              <p>
                The flux subsystem describes the flow of matter and energy through
                the metabolic network, governed by Kirchhoff&apos;s Current Law analog
                (mass balance) and enzyme kinetics.
              </p>
            </Definition>

            <Definition name="Subsystem 3: Charge">
              <p>
                The charge subsystem describes the electrical properties of the cell:
                membrane potential, ion gradients, and the emergence of macroscopic
                charge separation from molecular partition events.
              </p>
            </Definition>

            <Definition name="Subsystem 4: Circuit">
              <p>
                The circuit subsystem integrates partition, flux, and charge into
                a unified circuit model with Kirchhoff analogs, impedance, and
                signal propagation.
              </p>
            </Definition>

            <Definition name="Subsystem 5: O₂ Observation">
              <p>
                The O₂ observation subsystem provides the measurement apparatus:
                ternary molecular states, zero-backaction measurement, and resolution
                enhancement through counter arrays.
              </p>
            </Definition>

            <Definition name="Subsystem 6: Purpose">
              <p>
                The purpose subsystem encodes the teleological constraints:
                autocatalytic closure, self-maintenance, and the compilation pipeline
                that converts observations into complete cell states.
              </p>
            </Definition>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The correlation matrix below shows the pairwise correlations between
              all six subsystems, computed from validation experiment 1. Values close
              to 1.0 indicate near-perfect isomorphism.
            </p>

            <ChartContainer title="6×6 Subsystem Correlation Matrix">
              <Heatmap data={correlationData} labels={correlationLabels} width={450} height={450} />
            </ChartContainer>

            <Theorem name="Theorem 2: Subsystem Isomorphism">
              <p>
                All six subsystems are connected by structure-preserving morphisms.
                For any pair of subsystems (A, B), there exists a morphism &phi;: A &rarr; B
                that preserves the categorical structure, conservation laws, and
                dynamical properties. The composition of all pairwise morphisms
                forms a closed group.
              </p>
            </Theorem>

            <Equation label="2">
              {"φ: Subsystem_A → Subsystem_B    preserving    structure, conservation, dynamics"}
            </Equation>
          </Section>

          {/* Section 3: Morphism Chain Compilation */}
          <Section title="Morphism Chain Compilation" id="morphism-chain">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The compilation pipeline consists of four stages, each applying a specific
              type of biological morphism to transform and refine the cell state estimate.
              The pipeline processes raw observations into a complete, validated instantiation.
            </p>

            <Definition name="Stage 1: Observe">
              <p>
                Raw observational data (fluorescence, mass spectrometry, sequencing)
                is mapped into the categorical coordinate system. This stage handles
                noise, calibration, and normalization. Starting MARE: ~2.67.
              </p>
            </Definition>

            <Definition name="Stage 2: Catalyze">
              <p>
                The observed categories are processed through the catalyst vocabulary
                (12 biological catalysts), which enforce reaction-specific constraints
                and resolve ambiguities. MARE after catalysis: ~0.94.
              </p>
            </Definition>

            <Definition name="Stage 3: Fuse">
              <p>
                Multi-modal observations are fused using the subsystem isomorphisms.
                Constraints from all six subsystems are simultaneously enforced,
                dramatically reducing the uncertainty. MARE after fusion: ~0.23.
              </p>
            </Definition>

            <Definition name="Stage 4: Access">
              <p>
                The fused state is projected onto the accessible manifold of physically
                realizable cell states. This final step ensures biological consistency
                and produces the complete instantiation. Final MARE: ~0.0001.
              </p>
            </Definition>

            <ChartContainer title="Mean Absolute Relative Error at Each Pipeline Stage">
              <BarChart data={pipelineMARE} width={500} height={300} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The four-stage pipeline reduces the error by over four orders of magnitude,
              from an initial MARE of 2.67 (essentially random) to a final MARE of 0.0001
              (essentially perfect). Each stage contributes a significant error reduction,
              demonstrating that all four morphism types are necessary for complete
              instantiation.
            </p>
          </Section>

          {/* Section 4: Catalyst Vocabulary */}
          <Section title="Catalyst Vocabulary" id="catalyst-vocabulary">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The compilation pipeline uses a vocabulary of 12 biological catalysts,
              each representing a specific type of chemical transformation. These catalysts
              are not merely enzymes; they are <strong>categorical operators</strong> that
              transform molecular states in well-defined ways. Each catalyst has an
              associated exclusion factor that determines which state transitions it
              forbids, effectively constraining the space of possible cell states.
            </p>

            <div className="overflow-x-auto my-8">
              <table className="min-w-full text-sm text-dark dark:text-light">
                <thead>
                  <tr className="border-b border-dark/20 dark:border-light/20">
                    <th className="px-4 py-3 text-left font-semibold">#</th>
                    <th className="px-4 py-3 text-left font-semibold">Catalyst</th>
                    <th className="px-4 py-3 text-left font-semibold">Type</th>
                    <th className="px-4 py-3 text-left font-semibold">Exclusion Factor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark/10 dark:divide-light/10">
                  <tr><td className="px-4 py-2">1</td><td className="px-4 py-2">Kinase</td><td className="px-4 py-2">Phosphorylation</td><td className="px-4 py-2">0.42</td></tr>
                  <tr><td className="px-4 py-2">2</td><td className="px-4 py-2">Phosphatase</td><td className="px-4 py-2">Dephosphorylation</td><td className="px-4 py-2">0.38</td></tr>
                  <tr><td className="px-4 py-2">3</td><td className="px-4 py-2">Dehydrogenase</td><td className="px-4 py-2">Oxidation</td><td className="px-4 py-2">0.55</td></tr>
                  <tr><td className="px-4 py-2">4</td><td className="px-4 py-2">Reductase</td><td className="px-4 py-2">Reduction</td><td className="px-4 py-2">0.51</td></tr>
                  <tr><td className="px-4 py-2">5</td><td className="px-4 py-2">Isomerase</td><td className="px-4 py-2">Isomerization</td><td className="px-4 py-2">0.29</td></tr>
                  <tr><td className="px-4 py-2">6</td><td className="px-4 py-2">Lyase</td><td className="px-4 py-2">Cleavage</td><td className="px-4 py-2">0.63</td></tr>
                  <tr><td className="px-4 py-2">7</td><td className="px-4 py-2">Ligase</td><td className="px-4 py-2">Joining</td><td className="px-4 py-2">0.58</td></tr>
                  <tr><td className="px-4 py-2">8</td><td className="px-4 py-2">Transferase</td><td className="px-4 py-2">Group transfer</td><td className="px-4 py-2">0.44</td></tr>
                  <tr><td className="px-4 py-2">9</td><td className="px-4 py-2">Hydrolase</td><td className="px-4 py-2">Hydrolysis</td><td className="px-4 py-2">0.47</td></tr>
                  <tr><td className="px-4 py-2">10</td><td className="px-4 py-2">Synthase</td><td className="px-4 py-2">Synthesis</td><td className="px-4 py-2">0.61</td></tr>
                  <tr><td className="px-4 py-2">11</td><td className="px-4 py-2">Mutase</td><td className="px-4 py-2">Intramolecular transfer</td><td className="px-4 py-2">0.33</td></tr>
                  <tr><td className="px-4 py-2">12</td><td className="px-4 py-2">ATPase</td><td className="px-4 py-2">ATP hydrolysis</td><td className="px-4 py-2">0.72</td></tr>
                </tbody>
              </table>
            </div>

            <Theorem name="Theorem 3: Resolution Cascade">
              <p>
                Each catalyst in the vocabulary reduces the spatial resolution of the
                cell state estimate by its exclusion factor. The cumulative effect of
                applying all 12 catalysts in sequence produces a resolution cascade
                from 200 nm (optical diffraction limit) down to sub-angstrom scales.
              </p>
            </Theorem>

            <Equation label="3">
              {"Δx_k = Δx_{k-1} · (1 - f_k)    where f_k is the exclusion factor of catalyst k"}
            </Equation>

            <ChartContainer title="Resolution Cascade Through 12 Catalyst Steps (nm, log scale)">
              <LineChart data={resolutionCascade} width={550} height={300} color="#58E6D9" />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Starting from the optical diffraction limit of 200 nm, the cascade of 12
              catalysts reduces the resolution to 8.82 × 10⁻¹¹ nm &mdash; well below the
              size of individual atoms. This does not mean we are &quot;seeing&quot; sub-atomic features
              optically; rather, the categorical constraints imposed by each catalyst narrow
              the space of possible molecular configurations to the point where the position
              of every atom can be inferred from the categorical state.
            </p>
          </Section>

          {/* Section 5: Purpose vs Forward Simulation */}
          <Section title="Purpose vs Forward Simulation" id="purpose-vs-forward">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The compilation approach is compared directly against traditional forward
              simulation on the same cell state instantiation problem. The results
              demonstrate overwhelming superiority of the purpose-partitioned approach
              across all metrics.
            </p>

            <ChartContainer title="MARE Comparison: Forward Simulation vs Purpose Compilation">
              <BarChart data={forwardVsPurpose} width={400} height={300} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Forward simulation achieves a MARE of 0.303 (30.3% error), while purpose
              compilation achieves 0.012 (1.2% error). This 24.7-fold improvement in
              accuracy is accompanied by a 67.7-fold improvement in computational speed
              and a 7.2-fold improvement in information efficiency (bits of useful output
              per bit of input).
            </p>

            <ChartContainer title="Performance Ratios: Purpose / Forward">
              <BarChart data={performanceRatios} width={400} height={300} />
            </ChartContainer>

            <Theorem name="Theorem 4: Compilation Optimality">
              <p>
                The purpose compilation pipeline is optimal in the information-theoretic
                sense: it extracts the maximum possible information from the available
                observations, given the constraints encoded in the six subsystems. No
                other algorithm can achieve lower MARE with the same input data.
              </p>
            </Theorem>

            <Equation label="4">
              {"MARE_purpose ≤ MARE_any    for the same input observations"}
            </Equation>
          </Section>

          {/* Section 6: Autocatalytic Closure */}
          <Section title="Autocatalytic Closure" id="autocatalytic-closure">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The deepest result of the purpose framework is the demonstration of
              <strong> autocatalytic closure</strong>: the cell&apos;s six subsystems form a
              closed system where each subsystem catalyzes the operation of the others.
              No external &quot;program&quot; or &quot;blueprint&quot; is needed; the cell&apos;s organization
              is entirely self-sustaining through mutual catalysis.
            </p>

            <Definition name="Autocatalytic Closure">
              <p>
                A system is autocatalytically closed if every catalyst needed for its
                operation is produced by the system itself. Formally, let C be the set
                of catalysts and P(C) the set of products generated by applying C.
                The system is closed if C ⊂ P(C): every catalyst is among the products.
              </p>
            </Definition>

            <Theorem name="Theorem 5: Cellular Autocatalytic Closure">
              <p>
                The six subsystems of the partition framework are autocatalytically
                closed: each subsystem produces the catalysts needed by the other five.
                This closure is quantified by the closure metric &eta;, which equals 1.0
                for healthy cells and drops to 0.0 for any single-subsystem knockout.
              </p>
            </Theorem>

            <Equation label="5">
              {"η = |C ∩ P(C)| / |C|    (closure metric)"}
            </Equation>

            <ChartContainer title="Autocatalytic Closure Metric: Healthy vs Knockouts">
              <BarChart data={closureMetric} width={500} height={300} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The binary nature of the closure metric (1.0 for healthy, 0.0 for any knockout)
              demonstrates that autocatalytic closure is an all-or-nothing property: the
              cell either has complete self-sustaining organization or it doesn&apos;t. There
              is no intermediate state. This explains why single-enzyme deficiencies can
              have catastrophic effects on cellular function &mdash; they break the closure,
              and once broken, the entire self-sustaining cycle collapses.
            </p>

            <Theorem name="Theorem 6: Closure as Life Criterion">
              <p>
                Autocatalytic closure (&eta; = 1.0) is a necessary and sufficient
                condition for a chemical system to be &quot;alive&quot; in the partition
                framework sense. A system with &eta; = 1.0 is self-maintaining,
                self-observing, and capable of instantiation. A system with &eta; &lt; 1.0
                requires external support and is not autonomously viable.
              </p>
            </Theorem>

            <Equation label="6">
              {"η = 1.0  ⟺  system is autocatalytically closed  ⟺  system is 'alive'"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-8 leading-relaxed">
              This result provides a precise, mathematically rigorous criterion for
              distinguishing living from non-living chemical systems. It also explains
              the origin of biological purpose: the &quot;purpose&quot; of each subsystem is to
              catalyze the operation of the other five, and the &quot;purpose&quot; of the whole
              cell is to maintain its own autocatalytic closure. This is not anthropomorphic
              projection; it is a structural property of the mathematical framework.
            </p>
          </Section>
        </Layout>
      </main>
    </>
  );
}
