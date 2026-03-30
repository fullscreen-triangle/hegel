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

const partitionCapacityData = Array.from({ length: 10 }, (_, i) => ({
  x: i + 1,
  y: 2 * (i + 1) * (i + 1),
}));

const resolutionVsCounters = Array.from({ length: 20 }, (_, i) => ({
  x: i + 1,
  y: 1.0 / Math.sqrt(i + 1),
}));

const validationMetrics = [
  { label: "Backaction", value: 0.000168 },
  { label: "Velocity Error", value: 0.00032 },
  { label: "S-entropy Sum", value: 0.9998 },
  { label: "Displacement", value: 0.00015 },
];

export default function ObservationEquations() {
  return (
    <>
      <Head>
        <title>Observation Equations | Partition Framework</title>
        <meta
          name="description"
          content="Oxygen categorical microscopy using ternary molecular states. Zero-backaction measurement, cellular capacitor architecture, and resolution enhancement through counter arrays."
        />
      </Head>

      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Oxygen Categorical Microscopy"
            className="mb-16 !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
          />

          <p className="text-lg mb-16 text-dark/80 dark:text-light/80 leading-relaxed max-w-4xl mx-auto">
            The observation equations framework establishes a rigorous mathematical
            basis for measuring cellular states without disturbing them. By exploiting
            the categorical structure of molecular oxygen states, we achieve
            zero-backaction measurement &mdash; the biological equivalent of quantum
            non-demolition measurement. This enables imaging at resolutions far
            beyond classical diffraction limits through counter array architectures.
          </p>

          {/* Section 1: Axiomatic Foundations */}
          <Section title="Axiomatic Foundations" id="axioms">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The framework rests on two fundamental axioms that constrain the
              structure of biological observation. These axioms are not assumptions
              in the usual sense; they are structural necessities imposed by the
              physics of molecular systems.
            </p>

            <Theorem name="Axiom 1: Bounded Phase Space">
              <p>
                Every biological system occupies a bounded region of phase space.
                The state space of a cell is finite-dimensional and compact: there
                exists a maximum number of distinguishable states M_max determined
                by the physical constraints of molecular packing, energy availability,
                and chemical stability.
              </p>
            </Theorem>

            <Equation label="1">
              {"Ω_cell ⊂ ℝ^N    with    |Ω_cell| ≤ M_max < ∞"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This axiom has profound consequences: it means that the cell&apos;s state space
              can be partitioned into a finite number of categories, each containing a
              set of physically indistinguishable microstates. This partition structure
              is what gives rise to the categorical framework.
            </p>

            <Theorem name="Axiom 2: Categorical Observation">
              <p>
                Every observation of a biological system is mediated by a categorical
                projection: the observer does not access individual microstates but
                only the category to which the current state belongs. The observation
                operator O_cat maps states to categories.
              </p>
            </Theorem>

            <Equation label="2">
              {"Ô_cat: Ω_cell → Categories    with    Ô_cat(s) = Ô_cat(s')  ∀ s,s' ∈ same category"}
            </Equation>

            <Definition name="Partition Coordinates (n, ℓ, m, s)">
              <p>
                Each category in the cellular partition is labeled by four quantum-number-like
                indices: n (principal partition level, analogous to electron shells),
                ℓ (angular partition, encoding spatial organization),
                m (magnetic partition, encoding orientation), and
                s (spin partition, encoding internal state parity).
                The capacity of level n is:
              </p>
            </Definition>

            <Equation label="3">
              {"C(n) = 2n²    [categories per level]"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This capacity formula mirrors the electron shell capacity in atomic
              physics, and for deep structural reasons: both arise from the representation
              theory of the rotation group SO(3). The partition levels organize the
              cell&apos;s state space into a hierarchy of increasing complexity and information
              content.
            </p>

            <ChartContainer title="Partition Capacity C(n) = 2n² per Level">
              <LineChart data={partitionCapacityData} width={500} height={300} color="#58E6D9" />
            </ChartContainer>
          </Section>

          {/* Section 2: Physical-Categorical Commutation */}
          <Section title="Physical-Categorical Commutation" id="commutation">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The key property that enables zero-backaction measurement is the
              commutation of physical and categorical observables. Unlike quantum
              measurement, where observation generally disturbs the system, categorical
              observation in biological systems can be made non-perturbative.
            </p>

            <Theorem name="Theorem 1: Commutation of Observables">
              <p>
                The categorical observation operator commutes with all physical
                observables of the system:
              </p>
            </Theorem>

            <Equation label="4">
              {"[Ô_cat, Ô_phys] = Ô_cat · Ô_phys - Ô_phys · Ô_cat = 0"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This commutation relation means that measuring the categorical state
              of a molecule does not alter its physical state. The measurement extracts
              information without injecting energy or disturbing the dynamics. This is
              possible because the categorical projection is a <em>coarse-graining</em>
              operation: it discards microstate information that the physical dynamics
              do not depend on.
            </p>

            <Definition name="Zero-Backaction Measurement">
              <p>
                A measurement protocol has zero backaction if the post-measurement state
                is identical to the pre-measurement state in all physical observables.
                Formally: ⟨O_phys⟩_after = ⟨O_phys⟩_before for all physical observables
                O_phys. The categorical measurement achieves this because it operates on
                a different (commuting) sector of the observable algebra.
              </p>
            </Definition>

            <Theorem name="Theorem 2: S-Entropy Conservation">
              <p>
                During categorical observation, the total S-entropy is conserved:
              </p>
            </Theorem>

            <Equation label="5">
              {"S_k + S_t + S_e = S_total = const."}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where S_k is the kinetic entropy, S_t is the thermal entropy, and S_e
              is the electronic entropy. The observation merely redistributes entropy
              among these three sectors without changing the total. This conservation
              law is the fundamental guarantee of non-perturbative measurement.
            </p>
          </Section>

          {/* Section 3: Ternary State Framework */}
          <Section title="Ternary State Framework" id="ternary-states">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Molecular oxygen (O₂) provides the ideal probe for categorical microscopy
              because it naturally exists in three distinguishable states that correspond
              to its interaction with cellular components:
            </p>

            <Definition name="O₂ Ternary States">
              <p>
                |0⟩ = absorption state: O₂ bound to a receptor or enzyme active site.
                The molecule is captured and unavailable for other interactions.
              </p>
              <p className="mt-2">
                |1⟩ = ground state: O₂ freely dissolved in the cytoplasm.
                The molecule is available but not interacting.
              </p>
              <p className="mt-2">
                |2⟩ = emission state: O₂ being released from a binding site.
                The molecule carries information about the site it just left.
              </p>
            </Definition>

            <Equation label="6">
              {"O₂ states: |0⟩ absorption, |1⟩ ground, |2⟩ emission → log₂(3) ≈ 1.585 bits/molecule"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              A typical mammalian cell contains approximately 10⁹ dissolved O₂ molecules.
              Since each molecule carries log₂(3) ≈ 1.585 bits of categorical information,
              a single imaging cycle captures approximately 1.585 × 10⁹ bits of information
              about the cell&apos;s internal state.
            </p>

            <ChartContainer title="Information Content per Imaging Cycle">
              <div className="flex items-center gap-8 flex-wrap justify-center">
                <GaugeChart value={1.585} max={2} label="bits/molecule" width={180} height={180} />
                <GaugeChart value={1.59} max={2} label="Gbits/cycle (×10⁹)" width={180} height={180} />
              </div>
            </ChartContainer>

            <Theorem name="Theorem 3: Ternary Completeness">
              <p>
                The three O₂ states form a complete basis for categorical observation
                of any cellular process. Any metabolic, signaling, or regulatory event
                that consumes, produces, or redistributes O₂ is fully captured by
                the ternary state transitions.
              </p>
            </Theorem>

            <Equation label="7">
              {"P(|0⟩) + P(|1⟩) + P(|2⟩) = 1    (completeness)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The ternary completeness theorem guarantees that no information is lost
              in the categorical projection. Every physically relevant cellular event
              leaves a detectable signature in the O₂ state distribution. This is because
              oxygen is involved in virtually all metabolic processes, either as a direct
              participant (respiration, oxidases) or as an indirect indicator (via the
              redox state of the cell).
            </p>
          </Section>

          {/* Section 4: Cellular Capacitor Architecture */}
          <Section title="Cellular Capacitor Architecture" id="capacitor">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The cell&apos;s observation apparatus is organized as a capacitor: a charge-storing
              device that accumulates categorical information over time. The three &quot;plates&quot;
              of this biological capacitor are:
            </p>

            <Definition name="Biological Capacitor">
              <p>
                Membrane⁻ | Cytoplasm⁺ | O₂⁻
              </p>
              <p className="mt-2">
                The negatively charged membrane surface, the positively charged cytoplasmic
                medium (due to dissolved cations), and the electronegative O₂ molecules
                form a triple-layer capacitor with capacitance C ≈ 700 pF.
              </p>
            </Definition>

            <Equation label="8">
              {"C_cell ≈ ε₀ε_r A/d ≈ 700 pF"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where &epsilon;_r ≈ 80 (water dielectric constant), A ≈ 3000 &mu;m²
              (typical cell surface area), and d ≈ 3 nm (membrane thickness). This
              capacitance is large enough to store significant categorical information
              but small enough to be rapidly charged and discharged during each
              observation cycle.
            </p>

            <Theorem name="Theorem 4: Zero-Current Computation">
              <p>
                The categorical computation performed by the biological capacitor
                requires zero net current flow. Information is processed by charge
                redistribution within the capacitor plates, not by current flow
                through resistive elements. This means the computation is thermodynamically
                reversible in the categorical sector.
              </p>
            </Theorem>

            <Equation label="9">
              {"I_cat = dQ_cat/dt = 0    (zero categorical current)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              Zero-current computation is the biological realization of Landauer&apos;s principle
              in reverse: because the categorical observation does not erase information
              (it merely reads it), it does not dissipate the k_B T ln(2) per bit that
              Landauer&apos;s principle demands for information erasure.
            </p>
          </Section>

          {/* Section 5: Temperature as State Counting Rate */}
          <Section title="Temperature as State Counting Rate" id="temperature">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              In the categorical framework, temperature acquires a new interpretation:
              it is the rate at which the system transitions between distinguishable
              categorical states. Higher temperature means faster state transitions,
              which means more categorical information is generated per unit time.
            </p>

            <Definition name="Categorical Temperature">
              <p>
                T_cat = dM/dt, where M is the number of distinct categorical states
                visited by the system per unit time. This is related to the thermodynamic
                temperature by T = (k_B ln b)⁻¹ · T_cat, where b is the base of the
                categorical counting system.
              </p>
            </Definition>

            <Equation label="10">
              {"T_cat = dM/dt    [states/second]"}
            </Equation>

            <Theorem name="Theorem 5: Heat-Entropy Independence">
              <p>
                In the categorical framework, heat and entropy are independent quantities:
                the correlation between heat fluctuations and entropy changes vanishes
                in the categorical sector:
              </p>
            </Theorem>

            <Equation label="11">
              {"⟨δQ · ΔS⟩ = 0    (heat-entropy independence)"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This independence is a direct consequence of the commutation relation
              [O_cat, O_phys] = 0. Because categorical observations do not couple to
              thermal fluctuations, the entropy changes measured by the categorical
              apparatus are immune to thermal noise. This provides a fundamental
              advantage over conventional measurement techniques that are limited by
              thermal noise floors.
            </p>
          </Section>

          {/* Section 6: Resolution Enhancement */}
          <Section title="Resolution Enhancement" id="resolution">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The categorical microscopy framework achieves resolution enhancement
              through counter arrays: multiple independent or correlated O₂ counters
              that each provide an independent estimate of the cell&apos;s categorical state.
              By combining these estimates, the resolution improves beyond what any
              single counter could achieve.
            </p>

            <Theorem name="Theorem 6: Independent Counter Scaling">
              <p>
                For K independent counters, the spatial resolution improves as:
              </p>
            </Theorem>

            <Equation label="12">
              {"Δx_K = Δx₁ · K^(-1/2)    [independent counters]"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              This is the standard &radic;K improvement from averaging independent
              measurements. With 10⁹ O₂ molecules as independent counters, the
              resolution improves by a factor of ~31,600 over a single-molecule
              measurement.
            </p>

            <Theorem name="Theorem 7: Correlated Counter Enhancement">
              <p>
                When counters are correlated (as in enzymatic cascades where O₂
                binding events are structurally coupled), the resolution improves
                exponentially:
              </p>
            </Theorem>

            <Equation label="13">
              {"Δx_corr = Δx₁ · exp(-∑ ρ_ij)    [correlated counters]"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              where &rho;_ij is the correlation coefficient between counters i and j.
              For strongly correlated counter networks (as found in mitochondrial
              respiratory chains), the exponential enhancement can push the resolution
              far below the diffraction limit, approaching molecular-scale imaging.
            </p>

            <ChartContainer title="Resolution Improvement vs Number of Counters (K^(-1/2) scaling)">
              <LineChart data={resolutionVsCounters} width={500} height={300} color="#B63E96" />
            </ChartContainer>
          </Section>

          {/* Section 7: Electron Tracking Validation */}
          <Section title="Electron Tracking Validation" id="validation">
            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              The framework&apos;s predictions are validated through electron tracking
              experiments on the azurin protein, which undergoes a well-characterized
              Cu(I) &rarr; Cu(II) electron transfer. This system provides a clean
              test case because the electron transfer event is unambiguous and the
              associated O₂ state change is measurable.
            </p>

            <Definition name="Azurin Validation Protocol">
              <p>
                The blue copper protein azurin undergoes single-electron transfer
                between Cu(I) and Cu(II) states. The categorical observation framework
                predicts: (1) zero backaction on the transfer dynamics, (2) correct
                electron velocity, (3) conservation of total S-entropy, and (4)
                minimal displacement of the copper center.
              </p>
            </Definition>

            <ChartContainer title="Validation Metrics (Azurin Cu(I)→Cu(II) Transfer)">
              <BarChart data={validationMetrics} width={500} height={300} />
            </ChartContainer>

            <p className="text-dark/80 dark:text-light/80 mb-4 leading-relaxed">
              All four predictions are confirmed: the mean backaction is
              (1.68 ± 0.32) × 10⁻⁴ (effectively zero), the electron velocity
              matches quantum mechanical predictions, the S-entropy sum is conserved
              to within 0.02%, and the copper displacement is sub-angstrom.
            </p>

            <Theorem name="Theorem 8: Validation Completeness">
              <p>
                The azurin validation demonstrates that the categorical observation
                framework correctly predicts all measurable properties of single-electron
                transfer events. The framework is therefore validated for application
                to more complex biological systems where multiple electron and proton
                transfers occur simultaneously.
              </p>
            </Theorem>

            <Equation label="14">
              {"Mean backaction = (1.68 ± 0.32) × 10⁻⁴ ≈ 0    ✓"}
            </Equation>

            <Equation label="15">
              {"S_k + S_t + S_e = 0.9998 ≈ 1.0    ✓"}
            </Equation>

            <p className="text-dark/80 dark:text-light/80 mb-8 leading-relaxed">
              The near-perfect validation across all metrics confirms that categorical
              observation provides a faithful, non-perturbative window into molecular
              dynamics. The framework can now be applied with confidence to whole-cell
              imaging, where the enormous number of O₂ counters provides both the
              information bandwidth and the resolution enhancement needed for
              comprehensive cellular state determination.
            </p>
          </Section>
        </Layout>
      </main>
    </>
  );
}
