import Navbar from './navbar/page';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400">
      <Navbar />
      
      {/* Main Content */}
      <main className="pt-32 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold text-white mb-6">
            Welcome to Synaptiq
          </h1>
          <p className="text-xl text-white/90 mb-8">
            Experience the beauty of glassmorphic design
          </p>
          
          {/* Demo Card with Glassmorphism */}
          <div className="backdrop-blur-lg bg-white/10 border border-white/20 rounded-3xl p-8 shadow-2xl">
            <h2 className="text-3xl font-semibold text-white mb-4">
              Glassmorphic Card
            </h2>
            <p className="text-white/80">
              This is a demo card showcasing the glassmorphic effect with blur,
              transparency, and subtle borders.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
