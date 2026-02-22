import Link from "next/link";
import { Outfit } from "next/font/google";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export default function HomePage() {
  return (
    <main className={`${outfit.variable} font-landing min-h-screen flex flex-col`}>
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 backdrop-blur-xl bg-slate-950/80 border-b border-white/5">
        <span className="text-xl font-semibold bg-gradient-to-r from-cyan-300 to-violet-300 bg-clip-text text-transparent">
          RateMaster
        </span>
        <div className="flex items-center gap-6">
          <Link
            href="#features"
            className="px-4 py-2 text-slate-300 hover:text-white transition-colors rounded-lg hover:bg-white/5"
          >
            Features
          </Link>
          <Link
            href="/login"
            className="px-4 py-2 text-slate-300 hover:text-white transition-colors rounded-lg hover:bg-white/5"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="px-4 py-2 rounded-lg font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/30 transition-all"
          >
            Create Account
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 pt-24 pb-16 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-violet-500/5 pointer-events-none" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto text-center animate-fade-in">
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight mb-6">
            <span className="bg-gradient-to-r from-cyan-300 via-violet-300 to-emerald-300 bg-clip-text text-transparent">
              Revenue intelligence
            </span>
            <br />
            <span className="text-slate-100">for hotels</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Dual pricing engines, market signals, and ML-driven recommendations.
            See lift vs baseline, track applied rates, and export reports—all in
            one place.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/signup"
              className="glass-button glass-button-primary px-8 py-4 text-lg font-semibold"
            >
              Get started free
            </Link>
            <Link
              href="/login"
              className="glass-button px-8 py-4 text-lg border-white/20 text-slate-300 hover:text-white"
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-20 border-t border-white/5 scroll-mt-24">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-100 text-center mb-4">
            Built for revenue teams
          </h2>
          <p className="text-slate-400 text-center max-w-xl mx-auto mb-16">
            Everything you need to optimize rates, measure impact, and prove
            value.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: "Dual engines",
                desc: "Engine A for 0–30 days with BAR tiers. Engine B for 31–365 with floor/target/stretch calendar.",
              },
              {
                title: "Market signals",
                desc: "Competitor and demand data ingested on schedule. Confidence adjusts with signal freshness.",
              },
              {
                title: "Contribution tracking",
                desc: "Lift vs baseline, estimated GOP lift, flow-through. Applied vs not applied with avoided-losses.",
              },
              {
                title: "ML foundations",
                desc: "Feature store, model registry, training pipeline. Model version tagged on every prediction.",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="glass-card glass-card-hover p-6 rounded-xl animate-slide-up"
              >
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  {f.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-20 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <div className="glass-card p-12 rounded-2xl border-cyan-500/20 bg-gradient-to-b from-cyan-500/5 to-transparent">
            <h2 className="text-2xl font-bold text-slate-100 mb-4">
              Ready to optimize?
            </h2>
            <p className="text-slate-400 mb-8">
              Upload your data, run the engines, and start tracking lift.
            </p>
            <Link
              href="/signup"
              className="inline-block glass-button glass-button-primary px-8 py-4 text-lg font-semibold"
            >
              Create account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <span className="text-slate-500 text-sm">
              RateMaster · Revenue & pricing intelligence
            </span>
            <a
              href="#"
              className="flex items-center gap-2 text-slate-500 hover:text-slate-400 text-sm transition-colors"
            >
              <span>Powered by</span>
              <img
                src="/assets/flow.png"
                alt="Flow"
                className="h-6 w-auto object-contain"
              />
            </a>
          </div>
          <div className="flex gap-6">
            <Link
              href="#features"
              className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
            >
              Features
            </Link>
            <Link
              href="/login"
              className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
            >
              Create Account
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
