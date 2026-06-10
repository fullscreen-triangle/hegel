import Head from "next/head";
import dynamic from "next/dynamic";

const Sandbox = dynamic(() => import("@/components/sbs/Sandbox"), { ssr: false });

export default function SBSSandboxPage() {
  return (
    <>
      <Head>
        <title>SBS Sandbox — Systems Biology Shaders</title>
        <meta name="description" content="Write, compile, and observe metabolic circuits in the SBS domain-specific language." />
      </Head>
      <Sandbox />
    </>
  );
}
