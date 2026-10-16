

export const springEnter = {
  type: "spring" as const,
  stiffness: 400,
  damping: 30,
  mass: 0.8,
};


export const springModal = {
  type: "spring" as const,
  stiffness: 350,
  damping: 28,
};


export const springTab = {
  type: "spring" as const,
  stiffness: 500,
  damping: 35,
};


export const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -4 },
  transition: { duration: 0.15, ease: [0.16, 1, 0.3, 1] },
} as const;


export const staggerContainer = {
  animate: { transition: { staggerChildren: 0.04 } },
} as const;


export const staggerItem = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.12, ease: [0.16, 1, 0.3, 1] },
} as const;
