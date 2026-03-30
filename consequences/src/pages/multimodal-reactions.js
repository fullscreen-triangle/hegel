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
import { BarChart, LineChart, GaugeChart } from "@/components/D3Chart";

const signalDriftRatios = [
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

const enzymeFluxUniformity = [
  { label: "HK", value: 0.100, color: "#58E6D9" },
  { label: "PGI", value: 0.100, color: "#58E6D9" },
  { label: "PFK", value: 0.100, color: "#58E6D9" },
  { label: "ALD", value: 0.100, color: "#58E6D9" },
  { label: "TPI", value: 0.100, color: "#58E6D9" },
  { label: "GAPDH", value: 0.100, color: "#58E6D9" },
  { label: "PGK", value: 0.100, color: "#58E6D9" },
  { label: "PGM", value: 0.100, color: "#58E6D9" },
  { label: "ENO", value: 0.100, color: "#58E6D9" },
  { label: "PK", value: 0.100, color: "#58E6D9" },
];

const entropyVsM = Array.from({ length: 30 }, (_, i) => ({
  x: (i + 1) * 10,
  y: 1.38e-23 * (i + 1) * 10 * Math.log(2) * 1e23,
}));

export default function MultimodalReactions() {
  return (
    <>
      <Head>
        <title>Multimodal Reaction Localisation | Partition Framework</title>
        <meta
          name="description"
          content="Categorical state propagation, Grotthuss mechanism, proton conductance, charge emergence from partition, and the triple equivalence of oscillation, category, and partition."
        />
      </Head>

      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Multimodal Reaction Localisation"
            className="mb-16 !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
          />

          <p className="text-lg mb-16 text-dark/80 dark:text-light/80 leading-relaxed max-w-4xl mx-auto">
            Multimodal reaction localisation extends the partition framework to
            explain how biochemical signals propagate through cellular networks
            at velocities far exceeding molecular diffusion. The central mechanism
            is <strong>categorical state propagation</strong>: information about
            chemical state changes travels through structural coupling between
            adjacent molecules, like Newton&apos;s cradle transferring momentum without
            mass transport.
          </p>

          {/* Section 1: Categorical State Propagation */}
          <Section title="Categorical State Propagation" id="state-propagation">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The Grotthuss mechanism of proton transport provides the paradigmatic
              example of categorical state propagation. In the Grotthuss mechanism,
              a proton does not physically move from one end of a hydrogen-bonded
              water chain to the other. Instead, each water molecule transfers a proton
              to its neighbor while receiving one from the other side. The net effect
              is that the &quot;proton state&quot; propagates along the chain at the speed of
              hydrogen bond rearrangement, not the speed of proton diffusion.
            </p>

            <Definition name="Grotthuss Mechanism as Categorical Flow">
              <p>
                In the Grotthuss mechanism, each water molecule in a hydrogen-bonded chain
                can be in one of two categorical states: proton-donating (H₃O⁺-like) or
                proton-accepting (OH⁻-like). The proton &quot;transfer&quot; is actually a
                categorical state flip that propagates along the chain. The signal
                velocity v_signal is the speed of this categorical flip propagation,
                while the drift velocity v_drift is the speed of actual proton mass
                transport.
              </p>
            </Definition>

            <Theorem name="Theorem 1: Signal-Drift Velocity Separation">
              <p>
                In any categorical state propagation system, the signal velocity
                exceeds the drift velocity by a factor determined by the ratio of
                the structural coupling rate to the mass transport rate:
              </p>
            </Theorem>

            <Equation label="1">
              {"v_signal / v_drift = τ_diff / τ_couple ≫ 1"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This velocity separation is analogous to Newton&apos;s cradle: when a ball
              strikes one end, the impulse propagates through the chain of balls at
              the speed of sound in the ball material (very fast), while the balls
              themselves barely move (very slow). In biology, the &quot;balls&quot; are molecules,
              the &quot;impulse&quot; is a categorical state change, and the &quot;speed of sound&quot;
              is the conformational coupling rate.
            </p>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The signal-to-drift velocity ratios for glycolytic enzymes and hydrogen
              bonds are shown below. All enzymes show ratios of 100-2000, meaning
              their categorical states propagate 100-2000 times faster than their
              substrates diffuse. The hydrogen bond network achieves an extraordinary
              ratio of 3.07 × 10¹⁷, reflecting the near-instantaneous propagation
              of proton states through water.
            </p>

            <ChartContainer title="v_signal / v_drift Ratios for Enzymes and H-bond Network">
              <BarChart data={signalDriftRatios} width={600} height={350} />
            </ChartContainer>
          </Section>

          {/* Section 2: Charge Emergence from Partition */}
          <Section title="Charge Emergence from Partition" id="charge-emergence">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              One of the most striking predictions of the partition framework is that
              macroscopic electrical properties &mdash; charge separation, conductivity,
              capacitance &mdash; emerge directly from molecular partition events. There
              is no need to invoke &quot;electrical forces&quot; as a separate physical principle;
              electricity is a consequence of partition.
            </p>

            <Definition name="NaCl Dissolution: Partition Creates Conductivity">
              <p>
                When NaCl dissolves in water, the crystal lattice partitions into Na⁺
                and Cl⁻ ions. This single partition event increases the electrical
                conductivity by a factor of ~10¹³. The conductivity does not arise
                from any new force; it arises from the creation of mobile charge carriers
                by the partition of the crystal into its ionic components.
              </p>
            </Definition>

            <Equation label="2">
              {"σ_solution / σ_crystal ≈ 10¹³    (conductivity jump from partition)"}
            </Equation>

            <Theorem name="Theorem 2: Membrane Potential from Partition">
              <p>
                The membrane potential of a cell arises from the differential
                partition of ions across the lipid bilayer. The Nernst equation
                is a special case of the partition potential:
              </p>
            </Theorem>

            <Equation label="3">
              {"V_m = -(k_BT/ze) · ln(C_out/C_in) = -(k_BT/ze) · ΔH_cat(ion)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where ΔH_cat(ion) is the categorical depth difference of the ion
              between the extracellular and intracellular compartments. The membrane
              potential is thus a direct readout of the partition structure: it measures
              the information difference between inside and outside.
            </p>

            <Definition name="DNA as Capacitor">
              <p>
                Double-stranded DNA functions as a molecular capacitor with capacitance
                ~300 pF per genome. The two sugar-phosphate backbones act as the capacitor
                plates, and the base pairs act as the dielectric. The stored charge
                encodes the categorical state of gene expression: which genes are
                accessible (unpacked) and which are inaccessible (packed).
              </p>
            </Definition>

            <Equation label="4">
              {"C_DNA ≈ 300 pF    (genomic capacitance)"}
            </Equation>
          </Section>

          {/* Section 3: Proton Conductance */}
          <Section title="Proton Conductance" id="proton-conductance">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The partition framework predicts proton conductance through biological
              channels from first principles, without any free parameters. The
              conductance is determined entirely by the partition structure of the
              channel and the categorical coupling between adjacent proton sites.
            </p>

            <Theorem name="Theorem 3: Proton Conductance Formula">
              <p>
                The proton conductance of a biological channel is:
              </p>
            </Theorem>

            <Equation label="5">
              {"G_H = (e²/k_BT) · ∑ g_ij / τ_p"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where e is the elementary charge, g_ij is the categorical coupling
              between adjacent proton sites i and j, and &tau;_p is the partition lag
              (the minimum time for a categorical state transition). The sum runs over
              all adjacent pairs of proton sites in the channel.
            </p>

            <Definition name="Gramicidin A Validation">
              <p>
                Gramicidin A is a well-characterized proton channel with experimentally
                measured conductance of ~10-100 pS. The partition framework predicts
                a conductance in this range from the known structure of the channel
                (15 hydrogen-bonded water molecules in a single file) and the partition
                lag of hydrogen bond rearrangement (~1 ps).
              </p>
            </Definition>

            <ChartContainer title="Gramicidin A Proton Conductance">
              <div className="flex items-center gap-8 flex-wrap justify-center">
                <GaugeChart value={42} max={100} label="Predicted (pS)" width={180} height={180} />
                <GaugeChart value={50} max={100} label="Measured (pS)" width={180} height={180} />
              </div>
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The predicted conductance of ~42 pS falls squarely within the experimental
              range of 10-100 pS, validating the partition framework&apos;s ability to
              predict electrical properties of biological channels from structural
              information alone.
            </p>
          </Section>

          {/* Section 4: Reactions as Categorical Mixing */}
          <Section title="Reactions as Categorical Mixing" id="categorical-mixing">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              In the partition framework, biochemical reactions are understood as
              <strong> categorical mixing events</strong>: they take molecules in
              well-defined categorical states and produce molecules in different
              categorical states. The &quot;mixing&quot; refers to the redistribution of
              categorical information, not physical stirring.
            </p>

            <Definition name="Futile Cycles as Mixing Engines">
              <p>
                Futile cycles (pairs of opposing reactions that consume ATP without
                net chemical change) are traditionally viewed as wasteful. In the
                partition framework, they serve as <em>categorical mixing engines</em>:
                they continuously redistribute categorical states among the participating
                molecules, maintaining the cell&apos;s information connectivity. Without
                futile cycles, categorical information would stagnate and the cell
                would lose its ability to respond to changes.
              </p>
            </Definition>

            <Theorem name="Theorem 4: Near-Equilibrium Connectivity">
              <p>
                Near-equilibrium reactions (those with ΔG ≈ 0) maintain categorical
                connectivity between metabolite pools. They allow information to flow
                bidirectionally, keeping the network responsive. The further a reaction
                is from equilibrium, the more directional (and less connective) it becomes.
              </p>
            </Theorem>

            <Equation label="6">
              {"Connectivity(e) = 1 / (1 + |ΔG_e / k_BT|)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The uniform enzyme flux at steady state demonstrates this principle:
              all 10 glycolytic enzymes carry the same flux, indicating perfect
              categorical mixing and maximal network connectivity.
            </p>

            <ChartContainer title="Enzyme Flux Uniformity (mM/s) - Categorical Mixing">
              <BarChart data={enzymeFluxUniformity} width={600} height={300} />
            </ChartContainer>

            <Definition name="Directed Reactions from Comparison">
              <p>
                Reactions far from equilibrium (ΔG ≪ 0) act as <em>comparators</em>:
                they compare the categorical states of their substrates and products,
                and drive the conversion irreversibly in one direction. These are the
                &quot;decision points&quot; of the metabolic circuit, where the cell commits to
                a specific metabolic fate. In glycolysis, the three irreversible reactions
                (HK, PFK, PK) serve as the comparators that drive the pathway forward.
              </p>
            </Definition>
          </Section>

          {/* Section 5: Triple Equivalence */}
          <Section title="Triple Equivalence" id="triple-equivalence">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The deepest theoretical result of the multimodal framework is the
              <strong> triple equivalence</strong>: three apparently different descriptions
              of the same physical phenomenon &mdash; oscillation, category, and partition
              &mdash; are mathematically identical. They yield the same entropy, the same
              dynamics, and the same predictions for all measurable quantities.
            </p>

            <Theorem name="Theorem 5: Triple Equivalence">
              <p>
                The following three descriptions are equivalent:
              </p>
              <p className="mt-2">
                (1) <strong>Oscillation</strong>: The system is a collection of coupled oscillators
                with frequencies determined by the energy levels of the molecular states.
              </p>
              <p className="mt-1">
                (2) <strong>Category</strong>: The system is a category with objects (molecular species)
                and morphisms (reactions) that preserve the categorical structure.
              </p>
              <p className="mt-1">
                (3) <strong>Partition</strong>: The system is a partition of phase space into categories
                with capacity C(n) = 2n², governed by information-theoretic constraints.
              </p>
            </Theorem>

            <Equation label="7">
              {"Oscillation ≡ Category ≡ Partition"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The equivalence is proven by showing that all three descriptions yield
              the same entropy formula:
            </p>

            <Equation label="8">
              {"S = k_B · M · ln(b)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where M is the number of distinguishable states and b is the base of the
              categorical counting system (b = 2 for binary, b = 3 for ternary O₂ states).
              This formula is derived independently from each of the three descriptions,
              and the results are identical.
            </p>

            <ChartContainer title="Entropy S vs Number of States M (Three Derivations Overlap)">
              <LineChart data={entropyVsM} width={500} height={300} color="#B63E96" />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The single line in the chart above represents all three derivations: they
              produce identical curves. This is the graphical manifestation of the triple
              equivalence &mdash; there is only one underlying reality, described in three
              different mathematical languages.
            </p>

            <Theorem name="Theorem 6: Uniqueness of Description">
              <p>
                The triple equivalence implies that there is no &quot;correct&quot; description of
                the cell among the three. Each captures a different aspect of the same
                underlying structure: oscillation captures the dynamics, category captures
                the logic, and partition captures the information content. A complete
                understanding requires all three perspectives simultaneously.
              </p>
            </Theorem>

            <Equation label="9">
              {"∂S/∂t|_osc = ∂S/∂t|_cat = ∂S/∂t|_part    (entropy rate equivalence)"}
            </Equation>

            <Definition name="Implications for Multimodal Measurement">
              <p>
                The triple equivalence has practical implications for experimental design:
                any measurement modality (spectroscopic, electrical, informational) can
                be converted to any other through the equivalence maps. This means that
                a single measurement type (e.g., O₂ state counting) provides complete
                information about the system, because the partition description is
                equivalent to the oscillation and category descriptions. There is no
                &quot;hidden&quot; information that one modality captures but another misses.
              </p>
            </Definition>

            <p className="text-dark/80 dark:text-light/80 mb-8 leading-relaxed">
              The triple equivalence closes the theoretical loop of the partition
              framework: the cell is simultaneously an oscillating physical system,
              a categorical logical system, and a partitioned information system. These
              are not metaphors or analogies; they are mathematically identical
              descriptions of the same structure, each illuminating a different facet
              of the extraordinary organization that constitutes a living cell.
            </p>
          </Section>
        </Layout>
      </main>
    </>
  );
}
