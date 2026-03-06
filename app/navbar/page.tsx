"use client";

import Link from "next/link";
import { useState, useEffect, useCallback } from "react";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About" },
  { href: "/services", label: "Services" },
  { href: "/contact", label: "Contact" },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeLink, setActiveLink] = useState("/");

  const handleScroll = useCallback(() => {
    setScrolled(window.scrollY > 20);
  }, []);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? "py-2 px-4" : "py-4 px-6"
      }`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Glassmorphic Container */}
        <div
          className={`relative overflow-hidden rounded-2xl transition-all duration-500
            ${
              scrolled
                ? "bg-white/8 shadow-[0_8px_32px_rgba(0,0,0,0.4)] border border-white/15"
                : "bg-white/5 shadow-[0_4px_24px_rgba(0,0,0,0.2)] border border-white/12"
            }
          `}
          style={{ backdropFilter: "blur(20px) saturate(1.8)" }}
        >
          {/* Animated gradient border glow */}
          <div className="pointer-events-none absolute inset-0 rounded-2xl opacity-40">
            <div
              className="absolute -inset-px rounded-2xl"
              style={{
                background:
                  "linear-gradient(135deg, rgba(139,92,246,0.3), rgba(59,130,246,0.2), rgba(236,72,153,0.3))",
                mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                maskComposite: "exclude",
                padding: "1px",
              }}
            />
          </div>

          {/* Subtle inner light reflection */}
          <div
            className="pointer-events-none absolute inset-0 rounded-2xl opacity-30"
            style={{
              background:
                "radial-gradient(ellipse 60% 40% at 25% 0%, rgba(255,255,255,0.15), transparent)",
            }}
          />

          <div className="relative z-10 px-6 py-3.5 flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="group flex items-center gap-2.5">
              <div className="relative flex items-center justify-center w-9 h-9">
                <div
                  className="absolute inset-0 rounded-lg bg-linear-to-br from-violet-500 to-blue-500 opacity-80 group-hover:opacity-100 transition-opacity duration-300"
                  style={{ filter: "blur(0.5px)" }}
                />
                <div className="absolute inset-px rounded-[7px] bg-black/30 backdrop-blur-sm" />
                <svg
                  className="relative z-10 w-5 h-5 text-white transition-transform duration-300 group-hover:rotate-12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93" />
                  <path d="M8.56 13.44A4 4 0 1 0 12 18" />
                  <path d="M12 18a4 4 0 0 0 4-4c0-1.1-.45-2.1-1.17-2.83" />
                  <circle cx="12" cy="12" r="1.5" fill="currentColor" />
                </svg>
              </div>
              <span className="text-xl font-bold tracking-tight bg-linear-to-r from-white via-white to-white/70 bg-clip-text text-transparent transition-all duration-300 group-hover:to-violet-300">
                Synaptiq
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setActiveLink(href)}
                  className={`relative px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300
                    ${
                      activeLink === href
                        ? "text-white"
                        : "text-white/60 hover:text-white/90"
                    }
                  `}
                >
                  {activeLink === href && (
                    <span
                      className="absolute inset-0 rounded-xl bg-white/10 border border-white/8"
                      style={{
                        boxShadow:
                          "inset 0 1px 1px rgba(255,255,255,0.06), 0 0 12px rgba(139,92,246,0.15)",
                      }}
                    />
                  )}
                  <span className="absolute inset-0 rounded-xl bg-white/0 hover:bg-white/6 transition-colors duration-300" />
                  <span className="relative z-10">{label}</span>
                </Link>
              ))}
            </div>

            {/* CTA + Mobile Toggle */}
            <div className="flex items-center gap-3">
              <Link
                href="/get-started"
                className="hidden md:inline-flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.03] active:scale-[0.98]"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(139,92,246,0.6), rgba(59,130,246,0.6))",
                  boxShadow:
                    "0 0 20px rgba(139,92,246,0.25), inset 0 1px 1px rgba(255,255,255,0.15)",
                  border: "1px solid rgba(255,255,255,0.12)",
                }}
              >
                Get Started
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </Link>

              {/* Hamburger */}
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="md:hidden relative w-10 h-10 flex items-center justify-center rounded-xl bg-white/6 border border-white/10 hover:bg-white/10 transition-all duration-300"
                aria-label="Toggle menu"
              >
                <div className="w-5 flex flex-col items-center gap-1.25">
                  <span
                    className={`block h-0.5 w-full bg-white rounded-full transition-all duration-300 origin-center ${
                      isOpen ? "rotate-45 translate-y-1.75" : ""
                    }`}
                  />
                  <span
                    className={`block h-0.5 w-full bg-white rounded-full transition-all duration-300 ${
                      isOpen ? "opacity-0 scale-x-0" : ""
                    }`}
                  />
                  <span
                    className={`block h-0.5 w-full bg-white rounded-full transition-all duration-300 origin-center ${
                      isOpen ? "-rotate-45 -translate-y-1.75" : ""
                    }`}
                  />
                </div>
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          <div
            className={`md:hidden overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.33,1,0.68,1)] ${
              isOpen ? "max-h-100 opacity-100" : "max-h-0 opacity-0"
            }`}
          >
            <div className="px-6 pb-5 pt-2 border-t border-white/8">
              <div className="flex flex-col gap-1">
                {navLinks.map(({ href, label }, i) => (
                  <Link
                    key={href}
                    href={href}
                    onClick={() => {
                      setActiveLink(href);
                      setIsOpen(false);
                    }}
                    className={`relative px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                      activeLink === href
                        ? "text-white bg-white/8"
                        : "text-white/60 hover:text-white hover:bg-white/4"
                    }`}
                    style={{
                      transitionDelay: isOpen ? `${i * 50}ms` : "0ms",
                      transform: isOpen
                        ? "translateX(0)"
                        : "translateX(-12px)",
                      opacity: isOpen ? 1 : 0,
                    }}
                  >
                    {label}
                  </Link>
                ))}
                <div
                  className="mt-2 transition-all duration-300"
                  style={{
                    transitionDelay: isOpen
                      ? `${navLinks.length * 50}ms`
                      : "0ms",
                    transform: isOpen ? "translateX(0)" : "translateX(-12px)",
                    opacity: isOpen ? 1 : 0,
                  }}
                >
                  <Link
                    href="/get-started"
                    onClick={() => setIsOpen(false)}
                    className="flex items-center justify-center gap-2 w-full px-5 py-3 rounded-xl text-sm font-semibold text-white transition-all duration-300"
                    style={{
                      background:
                        "linear-gradient(135deg, rgba(139,92,246,0.5), rgba(59,130,246,0.5))",
                      border: "1px solid rgba(255,255,255,0.1)",
                    }}
                  >
                    Get Started
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M13 7l5 5m0 0l-5 5m5-5H6"
                      />
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
