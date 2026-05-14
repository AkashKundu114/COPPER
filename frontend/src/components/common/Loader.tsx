import { motion } from "framer-motion";

interface Props {
  size?: "sm" | "md" | "lg";
  text?: string;
}

const sizes = { sm: "w-4 h-4", md: "w-8 h-8", lg: "w-16 h-16" };

export function Loader({ size = "md", text }: Props) {
  return (
    <div className="flex flex-col items-center gap-3">
      <motion.div
        className={`${sizes[size]} rounded-full border-2 border-copper-600/30 border-t-copper-500`}
        animate={{ rotate: 360 }}
        transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
      />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  );
}
