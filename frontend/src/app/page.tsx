import { RepoForm } from "@/components/RepoForm";

export default function HomePage() {
  return (
      <main className="flex min-h-screen flex-col items-center justify-center p-12 overflow-hidden">
        {/* Background Gradient */}
        <div className="absolute inset-0 -z-10 h-full w-full bg-background bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]">
          <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-primary/20 opacity-50 blur-[100px]"></div>
        </div>

        <div className="text-center max-w-2xl">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/70">
            AI Code Documentation
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            Paste any public GitHub repository URL to analyze its structure,
            visualize dependencies, and generate comprehensive AI-powered
            documentation in real-time.
          </p>
        </div>

        <div className="w-full max-w-xl mt-12">
          <RepoForm />
        </div>
      </main>
  );
}