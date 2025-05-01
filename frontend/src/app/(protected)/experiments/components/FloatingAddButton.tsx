import { PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function FloatingAddButton() {
  return (
    <Button
      className="fixed bottom-10 right-10 rounded-full p-0 w-14 h-14 "
      aria-label="Add new item"
    >
      <PlusIcon className="h-6 w-6" />
    </Button>
  );
}
