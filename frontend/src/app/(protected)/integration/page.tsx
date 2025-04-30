import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiKeyDisplay } from "./components/ApiKeyDisplay";

export default function ApiKeyPage() {
  return (
    <div className="container mx-auto py-10 ">
      <Card>
        <CardHeader>
          <CardTitle>API Key Management</CardTitle>
          <CardDescription>
            View and manage your API keys securely
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ApiKeyDisplay />
        </CardContent>
      </Card>
    </div>
  );
}
