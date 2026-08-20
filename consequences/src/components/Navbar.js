import Link from "next/link";
import React, { useEffect, useRef, useState } from "react";
import Logo from "./Logo";
import { useRouter } from "next/router";
import {
  GithubIcon,
  LinkedInIcon,
  MoonIcon,
  SunIcon,
  TwitterIcon,
} from "./Icons";
import { motion } from "framer-motion";
import { useThemeSwitch } from "./Hooks/useThemeSwitch";

// One definition of the navigation, shared by the desktop bar and the mobile
// menu. The two used to carry independent copies of the same link list, which
// is how the HFQ page came to exist without appearing in either: there was no
// single place that adding a route would obviously touch.
//
// `items` present as a dropdown on desktop and as an indented block on mobile.
const NAV = [
  { href: "/", title: "Home" },
  {
    title: "Framework",
    items: [
      { href: "/fuzzy-circuits", title: "Fuzzy Circuits",
        blurb: "the circuit model" },
      { href: "/observation-equations", title: "Observation Equations",
        blurb: "what an observation is allowed to say" },
      { href: "/purpose-models", title: "Purpose Models",
        blurb: "purpose-partitioned compilation" },
      { href: "/multimodal-reactions", title: "Multimodal Reactions",
        blurb: "reaction localisation across modalities" },
    ],
  },
  {
    title: "Tools",
    items: [
      { href: "/hfq-notebook", title: "HFQ Notebook",
        blurb: "write a federated query plan and run it" },
      { href: "/sbs-tool", title: "SBS Tool",
        blurb: "systems biology shaders" },
      { href: "/sbs-playground", title: "SBS Playground",
        blurb: "edit and run shader programs" },
      { href: "/sbs-sandbox", title: "SBS Sandbox",
        blurb: "an unconstrained scratch surface" },
      { href: "/api-access", title: "API",
        blurb: "programmatic access" },
    ],
  },
  { href: "/subscriptions", title: "Plans" },
];

const CustomLink = ({ href, title, className = "" }) => {
  const router = useRouter();

  return (
    <Link href={href} className={`${className}  rounded relative group lg:text-light lg:dark:text-dark`}>
      {title}
      <span
        className={`
              inline-block h-[1px]  bg-dark absolute left-0 -bottom-0.5
              group-hover:w-full transition-[width] ease duration-300 dark:bg-light
              ${router.asPath === href ? "w-full" : " w-0"} lg:bg-light lg:dark:bg-dark
              `}
      >
        &nbsp;
      </span>
    </Link>
  );
};

const CustomMobileLink = ({ href, title, className = "", toggle }) => {
  const router = useRouter();

  const handleClick = () =>{
    toggle();
    router.push(href)
  }

  return (
    <button className={`${className}  rounded relative group lg:text-light lg:dark:text-dark`} onClick={handleClick}>
      {title}
      <span
        className={`
              inline-block h-[1px]  bg-dark absolute left-0 -bottom-0.5
              group-hover:w-full transition-[width] ease duration-300 dark:bg-light
              ${router.asPath === href ? "w-full" : " w-0"} lg:bg-light lg:dark:bg-dark
              `}
      >
        &nbsp;
      </span>
    </button>
  );
};



// A grouped menu for the desktop bar.
//
// The header underlines whenever any child route is active, so entering a
// submenu does not cost the reader their sense of where they are -- the flat
// bar got that from `router.asPath === href`, and a group has no href of its
// own to compare against.
const NavDropdown = ({ title, items, className = "" }) => {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const wrap = useRef(null);

  const active = items.some((i) => router.asPath === i.href);

  // Close on outside click and on Escape. A menu that only closes by clicking
  // its own trigger again traps the reader who opened it by mistake.
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (wrap.current && !wrap.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // Route changes close it too, otherwise the panel outlives the navigation
  // that was made from it.
  useEffect(() => {
    const close = () => setOpen(false);
    router.events.on("routeChangeComplete", close);
    return () => router.events.off("routeChangeComplete", close);
  }, [router.events]);

  return (
    <div ref={wrap} className={`${className} relative`}
         onMouseEnter={() => setOpen(true)}
         onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="rounded relative group lg:text-light lg:dark:text-dark
                   inline-flex items-center gap-1"
      >
        {title}
        <span className={`text-[0.6em] leading-none transition-transform duration-200
                          ${open ? "rotate-180" : ""}`}
              aria-hidden="true">
          &#9660;
        </span>
        <span
          className={`
              inline-block h-[1px] bg-dark absolute left-0 -bottom-0.5
              group-hover:w-full transition-[width] ease duration-300 dark:bg-light
              ${active ? "w-full" : "w-0"} lg:bg-light lg:dark:bg-dark
              `}
        >
          &nbsp;
        </span>
      </button>

      {/* The panel is always rendered and hidden with CSS rather than mounted
          on open. Unmounting it kept the nine sub-routes out of the prerendered
          HTML entirely, so a crawler -- or a reader without JS -- saw a site
          with four pages. `invisible` also takes them out of the tab order,
          which keeps the closed menu from swallowing keyboard focus. */}
      <div
        className={`absolute left-1/2 -translate-x-1/2 top-full pt-3 z-50 w-64
                    transition-opacity duration-150
                    ${open ? "opacity-100 visible"
                           : "opacity-0 invisible pointer-events-none"}`}
      >
        <ul className="rounded-lg border border-dark/15 dark:border-light/20
                       bg-light dark:bg-dark shadow-lg overflow-hidden py-1">
          {items.map((i) => {
            const here = router.asPath === i.href;
            return (
              <li key={i.href}>
                <Link
                  href={i.href}
                  onClick={() => setOpen(false)}
                  className={`block px-3 py-2 text-dark dark:text-light
                              hover:bg-dark/[0.06] dark:hover:bg-light/[0.10]
                              transition-colors ${here ? "bg-primary/10" : ""}`}
                >
                  <span className={`block text-sm ${here ? "font-bold" : "font-medium"}`}>
                    {i.title}
                  </span>
                  {i.blurb && (
                    <span className="block text-xs opacity-60 mt-0.5 font-normal">
                      {i.blurb}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};

const Navbar = () => {
  const [mode, setMode] = useThemeSwitch();
    const [isOpen, setIsOpen] = useState(false);

  const handleClick = () => {
    setIsOpen(!isOpen);
  };



  return (
    <header className="w-full flex items-center justify-between px-32 py-8 font-medium z-10 dark:text-light
    lg:px-16 relative z-1 md:px-12 sm:px-8
    ">

      <button
        type="button"
        className=" flex-col items-center justify-center hidden lg:flex"
        aria-controls="mobile-menu"
        aria-expanded={isOpen}
        onClick={handleClick}
      >
        <span className="sr-only">Open main menu</span>
        <span className={`bg-dark dark:bg-light block h-0.5 w-6 rounded-sm transition-all duration-300 ease-out ${isOpen ? 'rotate-45 translate-y-1' : '-translate-y-0.5'}`}></span>
        <span className={`bg-dark dark:bg-light block h-0.5 w-6 rounded-sm transition-all duration-300 ease-out ${isOpen ? 'opacity-0' : 'opacity-100'} my-0.5`}></span>
        <span className={`bg-dark dark:bg-light block h-0.5 w-6 rounded-sm transition-all duration-300 ease-out ${isOpen ? '-rotate-45 -translate-y-1' : 'translate-y-0.5'}`}></span>
      </button>

      <div className="w-full flex justify-between items-center lg:hidden"
      >
      <nav className="flex items-center justify-center">
        {NAV.map((entry, i) => {
          const spacing = i === 0 ? "mr-4"
            : i === NAV.length - 1 ? "ml-4" : "mx-4";
          return entry.items ? (
            <NavDropdown key={entry.title} className={spacing}
                         title={entry.title} items={entry.items} />
          ) : (
            <CustomLink key={entry.href} className={spacing}
                        href={entry.href} title={entry.title} />
          );
        })}
      </nav>
      <nav
        className="flex items-center justify-center flex-wrap lg:mt-2
      "
      >
        <motion.a
          target={"_blank"}
          className="w-6 mr-3"
          href="https://twitter.com"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Checkout my twitter profile"
        >
          <TwitterIcon />
        </motion.a>
        <motion.a
          target={"_blank"}
          className="w-6 mx-3"
          href="https://github.com/fullscreen-triangle"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Checkout my github profile"
        >
          <GithubIcon />
        </motion.a>
        <motion.a
          target={"_blank"}
          className="w-6 mx-3"
          href="https://linkedin.com"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Checkout my linkedin profile"
        >
          <LinkedInIcon />
        </motion.a>

        <button
          onClick={() => setMode(mode === "light" ? "dark" : "light")}
          className={`w-6 h-6 ease ml-3 flex items-center justify-center rounded-full p-1
            ${mode === "light" ? "bg-dark  text-light" : "bg-light  text-dark"}
            `}
          aria-label="theme-switcher"
        >
          {mode === "light" ? (
            <SunIcon className={"fill-dark"} />
          ) : (
            <MoonIcon className={"fill-dark"} />
          )}
        </button>
      </nav>
      </div>
    {
      isOpen ?

      <motion.div className="min-w-[70vw] sm:min-w-[90vw] flex justify-between items-center flex-col fixed top-1/2 left-1/2 -translate-x-1/2
      -translate-y-1/2
      py-32 bg-dark/90 dark:bg-light/75 rounded-lg z-50 backdrop-blur-md
      "
      initial={{scale:0,x:"-50%",y:"-50%", opacity:0}}
      animate={{scale:1,opacity:1}}
      >
      <nav className="flex items-center justify-center flex-col">
        {/* Groups are shown expanded rather than as tap-to-open menus. The
            panel is a deliberate full-screen interruption, so there is room to
            show every route, and hiding them behind a second tap would add a
            step without buying any space back. */}
        {NAV.map((entry) => entry.items ? (
          <div key={entry.title}
               className="flex flex-col items-center my-2 lg:my-1.5">
            <span className="text-light/50 dark:text-dark/50 text-xs uppercase
                             tracking-widest mb-1">
              {entry.title}
            </span>
            {entry.items.map((i) => (
              <CustomMobileLink key={i.href} toggle={handleClick}
                                className="lg:m-0 lg:my-1"
                                href={i.href} title={i.title} />
            ))}
          </div>
        ) : (
          <CustomMobileLink key={entry.href} toggle={handleClick}
                            className="lg:m-0 lg:my-2"
                            href={entry.href} title={entry.title} />
        ))}
      </nav>
      <nav
        className="flex items-center justify-center  mt-2
      "
      >
        <motion.a
          target={"_blank"}
          className="w-6 m-1 mr-3 sm:mx-1"
          href="https://twitter.com"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Checkout my twitter profile"
        >
          <TwitterIcon />
        </motion.a>
        <motion.a
          target={"_blank"}
          className="w-6 m-1 mx-3 bg-light rounded-full dark:bg-dark sm:mx-1"
          href="https://github.com/fullscreen-triangle"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Checkout my github profile"
        >
          <GithubIcon />
        </motion.a>
        <motion.a
          target={"_blank"}
          className="w-6 m-1 mx-3 sm:mx-1"
          href="https://linkedin.com"
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Checkout my linkedin profile"
        >
          <LinkedInIcon />
        </motion.a>

        <button
          onClick={() => setMode(mode === "light" ? "dark" : "light")}
          className={`w-6 h-6 ease m-1 ml-3 sm:mx-1 flex items-center justify-center rounded-full p-1
            ${mode === "light" ? "bg-dark  text-light" : "bg-light  text-dark"}
            `}
          aria-label="theme-switcher"
        >
          {mode === "light" ? (
            <SunIcon className={"fill-dark"} />
          ) : (
            <MoonIcon className={"fill-dark"} />
          )}
        </button>
      </nav>
      </motion.div>

      : null
    }

      <div className="absolute left-[50%] top-2 translate-x-[-50%] ">
        <Logo />
      </div>
    </header>
  );
};

export default Navbar;
