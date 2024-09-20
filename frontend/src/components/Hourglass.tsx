"use client";

import React from "react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function Hourglass() {
  const [flip, setFlip] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setFlip((prev) => !prev);
    }, 2000); // Flip every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <motion.svg
      xmlns="http://www.w3.org/2000/svg"
      width="100"
      height="100"
      viewBox="0 0 100 100"
      animate={{ rotateX: flip ? 180 : 0 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
    >
      {/* Hourglass outline */}
      <path
        d="M20,10 L80,10 L65,50 L80,90 L20,90 L35,50 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
      />

      {/* Upper chamber */}
      <motion.path
        d="M35,50 L20,10 L80,10 L65,50 Z"
        fill="currentColor"
        initial={{ clipPath: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)" }}
        animate={{
          clipPath: flip
            ? "polygon(0% 0%, 100% 0%, 100% 0%, 0% 0%)"
            : "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
        }}
        transition={{ duration: 2, ease: "linear" }}
      />

      {/* Lower chamber */}
      <motion.path
        d="M35,50 L20,90 L80,90 L65,50 Z"
        fill="currentColor"
        initial={{
          clipPath: "polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)",
        }}
        animate={{
          clipPath: flip
            ? "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)"
            : "polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)",
        }}
        transition={{ duration: 2, ease: "linear" }}
      />
    </motion.svg>
  );
}
