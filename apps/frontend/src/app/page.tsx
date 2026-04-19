import Link from "next/link";
import {
  ArrowRight,
  FileText,
  MessageSquare,
  Network,
  Search,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type QuickAction = {
  href: string;
  icon: typeof MessageSquare;
  title: string;
  description: string;
};

const quickActions: QuickAction[] = [
  {
    href: "/ask",
    icon: MessageSquare,
    title: "Ask a question",
    description: "Send a grounded query and inspect cited evidence.",
  },
  {
    href: "/documents",
    icon: FileText,
    title: "Upload document",
    description: "Parse and index a document for retrieval and ontology.",
  },
  {
    href: "/evidence",
    icon: Search,
    title: "Browse evidence",
    description: "Review citations, provenance, and source chunks.",
  },
  {
    href: "/ontology/builds",
    icon: Network,
    title: "Review ontology builds",
    description: "Approve candidate entities and publish graph versions.",
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Workspace</h1>
        <p className="text-sm text-muted-foreground">
          Knowledge operations cockpit for ask, documents, evidence, ontology,
          and graph.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {quickActions.map(({ href, icon: Icon, title, description }) => (
          <Link key={href} href={href} className="group">
            <Card className="h-full transition-colors group-hover:border-primary/50">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  {title}
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </section>
    </div>
  );
}
