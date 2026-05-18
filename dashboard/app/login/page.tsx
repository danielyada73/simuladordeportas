import { Lock } from "lucide-react";

type Props = { searchParams: Promise<{ from?: string; error?: string }> };

export default async function LoginPage({ searchParams }: Props) {
  const params = await searchParams;
  return (
    <div className="min-h-screen flex items-center justify-center bg-grid p-6">
      <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-medium/5 pointer-events-none" />
      <div className="relative w-full max-w-sm">
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent-soft flex items-center justify-center font-bold text-bg text-lg shadow-elevated">
              α
            </div>
            <div className="font-semibold text-lg">Alpha OS</div>
          </div>
        </div>
        <form
          action="/api/login"
          method="POST"
          className="card shadow-elevated p-7 space-y-5"
        >
          <div className="space-y-1">
            <h1 className="text-xl font-semibold">Acesso ao painel</h1>
            <p className="text-sm text-muted-strong">Apenas equipe da agência.</p>
          </div>
          <input type="hidden" name="from" value={params.from || "/"} />
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="password"
              name="password"
              placeholder="Senha"
              autoFocus
              className="w-full bg-bg border border-border rounded-lg pl-10 pr-3 py-2.5 focus:outline-none focus:border-accent transition-colors"
            />
          </div>
          {params.error && <p className="text-sm text-urgent">Senha inválida.</p>}
          <button
            type="submit"
            className="w-full bg-gradient-to-br from-accent to-accent-soft text-bg font-semibold rounded-lg py-2.5 hover:opacity-90 transition-opacity shadow-elevated"
          >
            Entrar
          </button>
        </form>
        <div className="text-center text-xs text-muted mt-4">
          Acesso individual de cliente é via link próprio.
        </div>
      </div>
    </div>
  );
}
