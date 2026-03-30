import React from "react";
import Layout from "./Layout";

const Footer = () => {
  return (
    <footer
      className="w-full border-t-2 border-solid border-dark
    font-medium text-lg dark:text-light dark:border-light sm:text-base
    "
    >
      <Layout className="py-8 flex items-center justify-between lg:flex-col lg:py-6">
        <span>&copy; 2024 Kundai Farai Sachikonye. Technical University of Munich.</span>

        <div className="flex items-center lg:py-2">
          School of Life Sciences
        </div>

        <span className="text-sm opacity-70">
          Partition Framework
        </span>
      </Layout>
    </footer>
  );
};

export default Footer;
