import { CMAB } from "../../types";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

export function CMABCards({
  experiment,
  isExpanded,
  setIsExpanded,
}: {
  experiment: CMAB;
  isExpanded: boolean;
  setIsExpanded: (isExpanded: boolean) => void;
}) {
  const { experiment_id, name, is_active, arms, contexts } = { ...experiment };
  const toggleExpand = () => setIsExpanded(!isExpanded);

  return (
    <div className="flex items-center justify-center">
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-40"
          />
        )}
      </AnimatePresence>

      <motion.div
        layout
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
        className={`${
          isExpanded
            ? "fixed flex inset-0 justify-center items-center col-span-3 z-50"
            : "w-full max-w-md"
        }`}
        onClick={() => {
          toggleExpand();
        }}
      >
        <Card
          className={`${
            isExpanded ? null : "cursor-pointer"
          } z-60 w-full max-w-[800px] dark:bg-black
                      dark:border-zinc-400 border-zinc-800 dark:shadown-zinc-600`}
          onClick={(e) => {
            e.stopPropagation();
            e.nativeEvent.stopImmediatePropagation();
            isExpanded ? null : toggleExpand();
          }}
        >
          <CardHeader className="flex flex-row items-start align-top justify-between space-y-0 pb-2">
            <div className="flex flex-col space-y-1">
              <CardTitle className="text-2xl font-bold">{name}</CardTitle>
              <CardDescription className="text-sm font-medium text-zinc-400 tracking-wider">
                ID: {experiment_id}
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2 pt-1">
              <div
                className={`w-3 h-3 rounded-full ${
                  is_active ? "bg-green-500" : "bg-gray-400"
                }`}
              />
              <span className="text-sm font-medium">
                {is_active ? "Active" : "Not Active"}
              </span>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col flex-between">
            <div className="mt-4">
              <div className="space-y-2">
                {!isExpanded &&
                  arms &&
                  arms.map((dist, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-24 text-sm">{dist.name}</div>
                      <div className="flex-1 h-4 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                        />
                      </div>
                      <div className="w-12 text-right text-sm">
                      </div>
                    </div>
                  ))}
                {!isExpanded &&
                  contexts &&
                  contexts.map((context, index) => (
                    <div key={index} className="flex items-center">
                      <div className="w-24 text-sm">{context.name}</div>
                      <div className="flex-1 h-4 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                        />
                      </div>
                      <div className="w-12 text-right text-sm">
                      </div>
                    </div>
                  ))}
              </div>
              <div className="flex flex-row justify-between mt-4">
                <div className="uppercase text-xs dark:text-neutral-400 font-medium mt-4">
                  Last Run: 2 days ago
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
