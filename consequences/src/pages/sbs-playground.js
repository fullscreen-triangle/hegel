import Head from 'next/head';
import Layout from '@/components/Layout';
import TransitionEffect from '@/components/TransitionEffect';
import dynamic from 'next/dynamic';

const PlaygroundEditor = dynamic(
  () => import('@/components/sbs/PlaygroundEditor'),
  { ssr: false }
);

export default function SBSPlayground() {
  return (
    <>
      <Head>
        <title>SBS Playground — Consequences</title>
        <meta name="description" content="Write, compile, and observe circuits in the SBS domain-specific language." />
      </Head>
      <TransitionEffect />
      <main className="w-full min-h-screen bg-light dark:bg-dark text-dark dark:text-light">
        <Layout className="!pt-4 !pb-0">
          <PlaygroundEditor />
        </Layout>
      </main>
    </>
  );
}
