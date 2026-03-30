import AnimatedText from "@/components/AnimatedText";
import { HireMe } from "@/components/HireMe";
import { LinkArrow } from "@/components/Icons";
import Layout from "@/components/Layout";
import Head from "next/head";
import Link from "next/link";
import TransitionEffect from "@/components/TransitionEffect";
import { motion } from "framer-motion";
import { StatCard } from "@/components/Section";
import dynamic from "next/dynamic";

const ModelViewer = dynamic(() => import("@/components/ModelViewer"), {
  ssr: false,
});

const SubsystemCard = ({ title, description, href, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    viewport={{ once: true }}
  >
    <Link href={href}>
      <div
        className="p-6 rounded-xl border border-dark/10 dark:border-light/10
        hover:border-primary dark:hover:border-primaryDark transition-colors duration-300
        hover:shadow-lg cursor-pointer h-full"
      >
        <h3 className="font-bold text-xl mb-3 text-dark dark:text-light">
          {title}
        </h3>
        <p className="text-dark/70 dark:text-light/70 text-sm leading-relaxed">
          {description}
        </p>
        <span className="inline-block mt-4 text-primary dark:text-primaryDark text-sm font-semibold">
          Read more &rarr;
        </span>
      </div>
    </Link>
  </motion.div>
);

export default function Home() {
  return (
    <>
      <Head>
        <title>
          Partition Framework | The Cell is a Self-Observing Categorical Circuit
        </title>
        <meta
          name="description"
          content="A unified mathematical framework proving that cells operate as self-observing categorical circuits. Fuzzy circuit models, oxygen microscopy, purpose-partitioned neural compilation, and multimodal reaction localisation."
        />
      </Head>

      <TransitionEffect />
      <article
        className={`flex flex-col min-h-screen items-center text-dark dark:text-light sm:items-start`}
      >
        <Layout className="!pt-0 md:!pt-16 sm:!pt-16">
          <div className="flex w-full items-start justify-between md:flex-col">
            <div className="w-1/2 lg:hidden md:inline-block md:w-full">
              <div className="h-[500px] md:h-[350px]">
                <ModelViewer />
              </div>
            </div>
            <div className="flex w-1/2 flex-col items-center self-center lg:w-full lg:text-center">
              <AnimatedText
                text="The Cell is a Self-Observing Categorical Circuit"
                className="!text-left !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
              />
              <p className="my-4 text-base font-medium md:text-sm sm:!text-xs">
                A unified mathematical framework demonstrating that biological
                cells operate as self-observing categorical circuits. By
                recasting chemical potential as categorical depth and applying
                information-theoretic foundations, we prove that cellular
                metabolism, signaling, and gene expression are isomorphic to
                electronic circuit behavior &mdash; with fuzzy logic, backward
                trajectories, and purpose-driven compilation.
              </p>
              <div className="mt-2 flex items-center self-start lg:self-center">
                <Link
                  href="/fuzzy-circuits"
                  className={`flex items-center rounded-lg border-2 border-solid bg-dark p-2.5 px-6 text-lg font-semibold
            capitalize text-light hover:border-dark hover:bg-transparent hover:text-dark
            dark:bg-light dark:text-dark dark:hover:border-light dark:hover:bg-dark dark:hover:text-light
            md:p-2 md:px-4 md:text-base
             `}
                >
                  Explore the Science{" "}
                  <LinkArrow className="ml-1 !w-6 md:!w-4" />
                </Link>

                <Link
                  href="https://github.com/fullscreen-triangle"
                  target="_blank"
                  className="ml-4 text-lg font-medium capitalize text-dark underline
                  dark:text-light md:text-base"
                >
                  View on GitHub
                </Link>
              </div>
            </div>
          </div>

          {/* Stats Section */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="grid grid-cols-4 gap-8 mt-32 md:grid-cols-2 md:mt-16 sm:gap-4"
          >
            <StatCard value="6" label="Unified Subsystems" />
            <StatCard value="22" label="Theorems Proven" />
            <StatCard value="12" label="Validation Experiments" />
            <StatCard value="All" label="Passed" />
          </motion.div>

          {/* Subsystem Overview */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="mt-32 md:mt-16"
          >
            <h2 className="font-bold text-6xl mb-16 text-center text-dark dark:text-light md:text-4xl md:mb-8">
              Framework Subsystems
            </h2>
            <div className="grid grid-cols-2 gap-8 lg:grid-cols-1 sm:gap-4">
              <SubsystemCard
                title="Fuzzy Circuit Model"
                description="Recasts cellular metabolism as an electronic circuit with Kirchhoff's Current and Voltage Law analogs. Fuzzy membership functions handle biological uncertainty while maintaining exact conservation laws. Backward trajectories enable disease detection via categorical address escape."
                href="/fuzzy-circuits"
                delay={0}
              />
              <SubsystemCard
                title="Observation Equations"
                description="Oxygen categorical microscopy using ternary molecular states (absorption, ground, emission). Zero-backaction measurement through physical-categorical commutation. Resolution enhancement via independent and correlated counter arrays."
                href="/observation-equations"
                delay={0.1}
              />
              <SubsystemCard
                title="Purpose-Partitioned Compilation"
                description="Solves the instantiation problem through compilation rather than forward simulation. The observe-catalyze-fuse-access pipeline achieves 24.7x better accuracy than forward approaches. Six subsystems proven isomorphic through morphism chain analysis."
                href="/purpose-models"
                delay={0.2}
              />
              <SubsystemCard
                title="Multimodal Reaction Localisation"
                description="Categorical state propagation explains Grotthuss-like mechanisms where signal velocity exceeds drift velocity by orders of magnitude. Proton conductance predictions match gramicidin A measurements. Triple equivalence: Oscillation = Category = Partition."
                href="/multimodal-reactions"
                delay={0.3}
              />
              <SubsystemCard
                title="API Access"
                description="RESTful API for cell state instantiation, disease detection, and drug design. Submit partial observations and receive complete cell states through the compilation pipeline."
                href="/api-access"
                delay={0.4}
              />
              <SubsystemCard
                title="Subscription Plans"
                description="Academic, Professional, and Enterprise tiers providing access to the framework's computational tools, organism-specific networks, and consulting services."
                href="/subscriptions"
                delay={0.5}
              />
            </div>
          </motion.div>
        </Layout>

        <HireMe />
      </article>
    </>
  );
}
