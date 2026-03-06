import Navbar from './navbar/page';

export default function Home() {
  return (
    <div
      className="min-h-screen"
      style={{ background: "linear-gradient(135deg, #ffffff 0%, #dbeafe 40%, #3b82f6 100%)" }}
    >
      <Navbar />

      {/* Main Content */}
      <main className="pt-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold text-slate-900 mb-6">
            Welcome to Synaptiq
          </h1>
          <p className="text-xl text-slate-600 mb-8">
            Experience the beauty of glassmorphic design
          </p>

          {/* Demo Card */}
          <div
            className="backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/80"
            style={{ background: "rgba(255,255,255,0.6)" }}
          >
            <h2 className="text-3xl font-semibold text-slate-800 mb-4">
              Glassmorphic Card
            </h2>
            <p className="text-slate-600">
              This is a demo card showcasing the glassmorphic effect with blur,
              transparency, and subtle borders.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
