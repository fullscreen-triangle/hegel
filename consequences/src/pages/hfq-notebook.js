import Head from 'next/head';
import dynamic from 'next/dynamic';
import Layout from '@/components/Layout';
import TransitionEffect from '@/components/TransitionEffect';

// The notebook executes a server-side Python interpreter through /api/hfq/run,
// so it has no meaningful server render; ssr is off rather than guarded.
const Notebook = dynamic(() => import('@/components/hfq/Notebook'), {
  ssr: false,
  loading: () => (
    <p className="font-mono text-sm opacity-50 py-8">loading the notebook…</p>
  ),
});

export default function HFQNotebook() {
  return (
    <>
      <Head>
        <title>HFQ Notebook — Consequences</title>
        <meta
          name="description"
          content="Write hegel federated query plans and execute them against local fixtures: capability check, budget allocation, six-valued verdicts and the lowered concrete query."
        />
      </Head>
      <TransitionEffect />
      <main className="w-full min-h-screen bg-light dark:bg-dark text-dark dark:text-light">
        <Layout className="!pt-4 !pb-8">
          <Notebook />
        </Layout>
      </main>
    </>
  );
}
