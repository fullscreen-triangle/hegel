import AnimatedText from "@/components/AnimatedText";
import Layout from "@/components/Layout";
import Head from "next/head";
import Link from "next/link";
import TransitionEffect from "@/components/TransitionEffect";
import { motion } from "framer-motion";

const CheckIcon = () => (
  <svg className="w-5 h-5 text-primaryDark flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const PricingCard = ({ title, price, period, features, cta, ctaLink, highlighted = false, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 40 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, delay }}
    viewport={{ once: true }}
    whileHover={{ y: -8, transition: { duration: 0.3 } }}
    className={`relative flex flex-col rounded-2xl p-8 shadow-lg ${
      highlighted
        ? "bg-dark text-light dark:bg-light dark:text-dark border-2 border-primary dark:border-primaryDark scale-105 md:scale-100 z-10"
        : "bg-light text-dark dark:bg-dark dark:text-light border border-dark/10 dark:border-light/10"
    }`}
  >
    {highlighted && (
      <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-primary dark:bg-primaryDark text-light text-sm font-semibold">
        Most Popular
      </div>
    )}
    <h3 className="text-2xl font-bold mb-2">{title}</h3>
    <div className="mb-6">
      <span className="text-4xl font-bold">{price}</span>
      {period && <span className="text-sm opacity-70 ml-1">{period}</span>}
    </div>
    <ul className="space-y-3 mb-8 flex-grow">
      {features.map((feature, i) => (
        <li key={i} className="flex items-start gap-3">
          <CheckIcon />
          <span className="text-sm opacity-90">{feature}</span>
        </li>
      ))}
    </ul>
    <Link
      href={ctaLink || "#"}
      className={`w-full text-center py-3 px-6 rounded-lg font-semibold transition-all duration-300 ${
        highlighted
          ? "bg-primary dark:bg-primaryDark text-light hover:opacity-90"
          : "bg-dark text-light dark:bg-light dark:text-dark hover:opacity-90"
      }`}
    >
      {cta}
    </Link>
  </motion.div>
);

const FAQ = ({ question, answer }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    viewport={{ once: true }}
    className="border-b border-dark/10 dark:border-light/10 py-6"
  >
    <h3 className="font-semibold text-lg mb-2 text-dark dark:text-light">{question}</h3>
    <p className="text-dark/70 dark:text-light/70 text-sm leading-relaxed">{answer}</p>
  </motion.div>
);

export default function Subscriptions() {
  return (
    <>
      <Head>
        <title>Subscription Plans | Partition Framework</title>
        <meta
          name="description"
          content="Choose your access tier for the Partition Framework. Academic, Professional, and Enterprise plans for cell state instantiation, disease detection, and drug design."
        />
      </Head>

      <TransitionEffect />
      <main className="flex w-full flex-col items-center justify-center dark:text-light">
        <Layout className="pt-16">
          <AnimatedText
            text="Choose Your Plan"
            className="mb-8 !text-6xl xl:!text-5xl lg:!text-center lg:!text-6xl md:!text-5xl sm:!text-3xl"
          />

          <p className="text-lg mb-16 text-dark/80 dark:text-light/80 leading-relaxed max-w-3xl mx-auto text-center">
            Access the partition framework&apos;s computational tools for cell state
            instantiation, disease detection, and drug design. Choose the plan
            that fits your research or business needs.
          </p>

          {/* Pricing Cards */}
          <div className="grid grid-cols-3 gap-8 items-start lg:grid-cols-1 lg:max-w-lg lg:mx-auto mb-32 md:mb-16">
            <PricingCard
              title="Academic"
              price="Free"
              period=""
              features={[
                "Access to published papers",
                "Basic API: 100 requests/day",
                "Single organism networks (E. coli)",
                "Community support via forums",
                "Basic instantiation endpoint",
                "Documentation access",
                "Open-source SDK access",
              ]}
              cta="Get Started"
              ctaLink="/api-access"
              delay={0}
            />
            <PricingCard
              title="Professional"
              price="$299"
              period="/month"
              features={[
                "Full API access: 10,000 requests/day",
                "All organism networks (E. coli, yeast, human)",
                "Disease detection module",
                "Drug design module",
                "Priority email support",
                "Intermediate pipeline results",
                "Custom confidence thresholds",
                "Batch processing up to 1,000 states",
                "Webhook notifications",
              ]}
              cta="Start Trial"
              ctaLink="/api-access"
              highlighted={true}
              delay={0.1}
            />
            <PricingCard
              title="Enterprise"
              price="Custom"
              period=""
              features={[
                "Unlimited API access",
                "Custom organism models",
                "On-premise deployment option",
                "Dedicated account manager",
                "Training & consulting sessions",
                "Custom integrations (LIMS, EHR)",
                "SLA guarantee (99.9% uptime)",
                "White-label solutions",
                "Priority feature requests",
                "Annual review & optimization",
              ]}
              cta="Contact Us"
              ctaLink="mailto:kundai.sachikonye@wzw.tum.de"
              delay={0.2}
            />
          </div>

          {/* Feature Comparison */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="mb-32 md:mb-16"
          >
            <h2 className="font-bold text-4xl mb-8 text-center text-dark dark:text-light md:text-3xl">
              Feature Comparison
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-dark dark:text-light">
                <thead>
                  <tr className="border-b-2 border-dark/20 dark:border-light/20">
                    <th className="px-4 py-3 text-left font-semibold">Feature</th>
                    <th className="px-4 py-3 text-center font-semibold">Academic</th>
                    <th className="px-4 py-3 text-center font-semibold text-primary dark:text-primaryDark">Professional</th>
                    <th className="px-4 py-3 text-center font-semibold">Enterprise</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark/10 dark:divide-light/10">
                  <tr>
                    <td className="px-4 py-3">Cell State Instantiation</td>
                    <td className="px-4 py-3 text-center">Basic</td>
                    <td className="px-4 py-3 text-center font-semibold">Full Pipeline</td>
                    <td className="px-4 py-3 text-center">Full + Custom</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Disease Detection</td>
                    <td className="px-4 py-3 text-center opacity-40">--</td>
                    <td className="px-4 py-3 text-center">Yes</td>
                    <td className="px-4 py-3 text-center">Yes + Custom</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Drug Design Module</td>
                    <td className="px-4 py-3 text-center opacity-40">--</td>
                    <td className="px-4 py-3 text-center">Yes</td>
                    <td className="px-4 py-3 text-center">Yes + Custom</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Organisms</td>
                    <td className="px-4 py-3 text-center">E. coli</td>
                    <td className="px-4 py-3 text-center">E. coli, Yeast, Human</td>
                    <td className="px-4 py-3 text-center">Custom Models</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Batch Processing</td>
                    <td className="px-4 py-3 text-center opacity-40">--</td>
                    <td className="px-4 py-3 text-center">1,000 states</td>
                    <td className="px-4 py-3 text-center">Unlimited</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Support</td>
                    <td className="px-4 py-3 text-center">Community</td>
                    <td className="px-4 py-3 text-center">Priority Email</td>
                    <td className="px-4 py-3 text-center">Dedicated Manager</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">Deployment</td>
                    <td className="px-4 py-3 text-center">Cloud</td>
                    <td className="px-4 py-3 text-center">Cloud</td>
                    <td className="px-4 py-3 text-center">Cloud + On-Premise</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">SLA</td>
                    <td className="px-4 py-3 text-center opacity-40">--</td>
                    <td className="px-4 py-3 text-center">99.5%</td>
                    <td className="px-4 py-3 text-center">99.9%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* FAQs */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="max-w-3xl mx-auto"
          >
            <h2 className="font-bold text-4xl mb-8 text-center text-dark dark:text-light md:text-3xl">
              Frequently Asked Questions
            </h2>

            <FAQ
              question="Can I use the Academic tier for published research?"
              answer="Yes. The Academic tier is free for all academic and non-commercial research. We only ask that you cite the partition framework papers in your publications. The Academic tier provides access to the basic instantiation endpoint and the E. coli metabolic network."
            />
            <FAQ
              question="What happens if I exceed my rate limit?"
              answer="If you exceed your daily rate limit, subsequent requests will receive a 429 (Too Many Requests) response with a Retry-After header indicating when you can make requests again. Your data and API key are not affected. Consider upgrading to a higher tier if you consistently hit the rate limit."
            />
            <FAQ
              question="Can I switch plans at any time?"
              answer="Yes. You can upgrade at any time and the change takes effect immediately. Downgrades take effect at the end of the current billing period. Pro-rated refunds are not available for downgrades."
            />
            <FAQ
              question="Is there a trial period for Professional?"
              answer="Yes. The Professional tier includes a 14-day free trial with full access to all features and 10,000 requests per day. No credit card required to start the trial."
            />
            <FAQ
              question="What organisms are supported?"
              answer="Currently supported: Escherichia coli (K-12 MG1655), Saccharomyces cerevisiae (S288C), and Homo sapiens (Recon3D). Enterprise customers can request custom organism models built from genome-scale metabolic reconstructions."
            />
            <FAQ
              question="How is data privacy handled?"
              answer="All API communications are encrypted via TLS 1.3. We do not store your input data beyond the processing window (typically <1 second). Enterprise customers can opt for on-premise deployment where no data leaves their infrastructure."
            />
          </motion.div>
        </Layout>
      </main>
    </>
  );
}
