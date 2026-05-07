import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-3xl font-semibold">Skate Assistant</h1>
      <p className="text-muted-foreground">Foundation scaffold — Story 1.1.</p>
      <Button>Pipeline check</Button>
    </main>
  );
}
