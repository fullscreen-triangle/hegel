import AnimatedText from "@/components/AnimatedText";
import Layout from "@/components/Layout";
import Head from "next/head";
import TransitionEffect from "@/components/TransitionEffect";
import dynamic from "next/dynamic";

const ModelViewer = dynamic(() => import("@/components/ModelViewer"), {
  ssr: false,
});

export default function Home() {
  return (
    <>
      <Head>
        <title>Consequences</title>
        <meta
          name="description"
          content="Consequences — a unified mathematical framework for biological observation via shader computing."
        />
      </Head>

      <TransitionEffect />
      <main className="flex flex-col min-h-[calc(100vh-80px)] items-center justify-center text-dark dark:text-light">
        <Layout className="!pt-0 flex flex-col items-center justify-center flex-1">
          <div className="flex flex-col items-center justify-center w-full max-w-3xl mx-auto">
            <div className="w-full" style={{ height: '55vh', minHeight: 350 }}>
              <ModelViewer />
            </div>
            <AnimatedText
              text="Consequences"
              className="!text-5xl mt-4 md:!text-4xl sm:!text-3xl"
            />
          </div>
        </Layout>
      </main>
    </>
  );
}
