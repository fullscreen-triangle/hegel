import { motion } from 'framer-motion';

export const Section = ({ title, children, id }) => (
  <motion.section
    id={id}
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6 }}
    viewport={{ once: true }}
    className="mb-16"
  >
    {title && (
      <h2 className="font-bold text-4xl mb-8 text-dark dark:text-light md:text-3xl sm:text-2xl">
        {title}
      </h2>
    )}
    {children}
  </motion.section>
);

export const Equation = ({ children, label }) => (
  <div className="my-6 p-4 bg-dark/5 dark:bg-light/5 rounded-lg overflow-x-auto">
    <div className="flex items-center justify-between">
      <code className="text-sm md:text-xs font-mono text-dark dark:text-light whitespace-pre">
        {children}
      </code>
      {label && <span className="text-xs text-dark/50 dark:text-light/50 ml-4">({label})</span>}
    </div>
  </div>
);

export const Theorem = ({ name, children }) => (
  <div className="my-6 border-l-4 border-primary dark:border-primaryDark pl-6">
    <h3 className="font-bold text-lg text-primary dark:text-primaryDark mb-2">{name}</h3>
    <div className="text-dark/90 dark:text-light/90">{children}</div>
  </div>
);

export const Definition = ({ name, children }) => (
  <div className="my-6 border-l-4 border-dark/30 dark:border-light/30 pl-6">
    <h3 className="font-semibold text-lg mb-2 text-dark dark:text-light">{name}</h3>
    <div className="text-dark/80 dark:text-light/80">{children}</div>
  </div>
);

export const ChartContainer = ({ title, children }) => (
  <div className="my-8 p-6 bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl shadow-sm">
    {title && <h3 className="font-semibold text-lg mb-4 text-dark dark:text-light">{title}</h3>}
    <div className="flex justify-center overflow-x-auto">{children}</div>
  </div>
);

export const StatCard = ({ value, label, unit = '' }) => (
  <motion.div
    whileHover={{ scale: 1.05 }}
    className="p-6 rounded-xl bg-dark text-light dark:bg-light dark:text-dark text-center shadow-lg"
  >
    <div className="text-3xl font-bold md:text-2xl">{value}<span className="text-lg">{unit}</span></div>
    <div className="text-sm mt-2 opacity-80">{label}</div>
  </motion.div>
);
