import Head from 'next/head';
import Layout from '@/components/Layout';
import TransitionEffect from '@/components/TransitionEffect';
import AnimatedText from '@/components/AnimatedText';
import { SBSProvider, useSBS } from '@/components/sbs/SBSContext';
import CircuitSearch from '@/components/sbs/CircuitSearch';
import CircuitGraph from '@/components/sbs/CircuitGraph';
import CellModelPicker from '@/components/sbs/CellModelPicker';
import CellViewer from '@/components/sbs/CellViewer';
import ObservationPanel from '@/components/sbs/ObservationPanel';
import MetricsDashboard from '@/components/sbs/MetricsDashboard';
import PerturbationEditor from '@/components/sbs/PerturbationEditor';
import { motion } from 'framer-motion';

const steps = [
  { id: 'search', label: 'Define Circuit', num: 1 },
  { id: 'geometry', label: 'Spatial Geometry', num: 2 },
  { id: 'observe', label: 'Observe', num: 3 },
];

function StepIndicator() {
  const { step } = useSBS();
  const currentIdx = steps.findIndex(s => s.id === step);

  return (
    <div className="flex items-center justify-center mb-12 gap-2">
      {steps.map((s, i) => {
        const active = i <= currentIdx;
        return (
          <div key={s.id} className="flex items-center gap-2">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold
              transition-colors duration-300
              ${active
                ? 'bg-primary dark:bg-primaryDark text-light'
                : 'bg-dark/10 dark:bg-light/10 text-dark/40 dark:text-light/40'}
            `}>
              {s.num}
            </div>
            <span className={`text-sm font-medium hidden sm:inline ${
              active ? 'text-dark dark:text-light' : 'text-dark/40 dark:text-light/40'
            }`}>
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <div className={`w-12 h-0.5 mx-2 transition-colors duration-300 ${
                i < currentIdx ? 'bg-primary dark:bg-primaryDark' : 'bg-dark/10 dark:bg-light/10'
              }`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StepContent() {
  const { step } = useSBS();

  return (
    <div className="min-h-[600px]">
      {step === 'search' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <CircuitSearch />
            <CircuitGraph />
          </div>
        </motion.div>
      )}

      {step === 'geometry' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <CellModelPicker />
            <CellViewer />
          </div>
        </motion.div>
      )}

      {step === 'observe' && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="space-y-8">
            <ObservationPanel />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <MetricsDashboard />
              <PerturbationEditor />
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function SBSToolContent() {
  return (
    <>
      <StepIndicator />
      <StepContent />
    </>
  );
}

export default function SBSTool() {
  return (
    <>
      <Head>
        <title>Systems Biology Shaders | Observation Tool</title>
        <meta name="description" content="GPU-native observation of cellular circuits via shader computing" />
      </Head>
      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center">
        <Layout className="pt-16">
          <AnimatedText
            text="Systems Biology Shaders"
            className="mb-4 lg:!text-5xl sm:!text-4xl xs:!text-3xl"
          />
          <p className="text-dark/70 dark:text-light/70 text-center mb-12 max-w-2xl mx-auto">
            Single-pass GPU observation of cellular circuits. Define a pathway, project onto cell geometry, observe.
          </p>
          <SBSProvider>
            <SBSToolContent />
          </SBSProvider>
        </Layout>
      </main>
    </>
  );
}
