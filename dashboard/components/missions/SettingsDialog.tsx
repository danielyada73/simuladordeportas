"use client";

import { X, Plus, Save } from "lucide-react";
import { useState, useTransition } from "react";
import { updateSettingsAction, upsertUserAction } from "@/app/missoes/actions";
import type { MissionUser, MissionSettings } from "@/lib/missions-types";

type Props = {
  open: boolean;
  onClose: () => void;
  users: MissionUser[];
  settings: MissionSettings;
};

export function SettingsDialog({ open, onClose, users, settings }: Props) {
  const [logoUrl, setLogoUrl] = useState(settings.logo_url || "");
  const [clientsText, setClientsText] = useState((settings.client_options || []).join("\n"));
  const [isPending, startTransition] = useTransition();
  const [feedback, setFeedback] = useState<string | null>(null);

  const [newSlug, setNewSlug] = useState("");
  const [newName, setNewName] = useState("");
  const [newPhoto, setNewPhoto] = useState("");

  const [editingPhotos, setEditingPhotos] = useState<Record<string, string>>(
    Object.fromEntries(users.map((u) => [u.slug, u.photo_url || ""]))
  );

  if (!open) return null;

  function saveSettings() {
    setFeedback(null);
    const list = clientsText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    startTransition(async () => {
      const res = await updateSettingsAction({
        logo_url: logoUrl.trim() || undefined,
        client_options: list,
      });
      if (res.ok) setFeedback("✓ Configurações salvas");
      else setFeedback(`Erro: ${res.error}`);
    });
  }

  function saveUserPhoto(slug: string) {
    setFeedback(null);
    startTransition(async () => {
      const res = await upsertUserAction({
        slug,
        display_name: users.find((u) => u.slug === slug)?.display_name || slug,
        photo_url: editingPhotos[slug] || undefined,
      });
      if (res.ok) setFeedback(`✓ Foto de ${slug} salva`);
      else setFeedback(`Erro: ${res.error}`);
    });
  }

  function addUser() {
    setFeedback(null);
    if (!newSlug.trim() || !newName.trim()) {
      setFeedback("Slug e nome são obrigatórios");
      return;
    }
    startTransition(async () => {
      const res = await upsertUserAction({
        slug: newSlug.trim().toLowerCase(),
        display_name: newName.trim(),
        photo_url: newPhoto.trim() || undefined,
      });
      if (res.ok) {
        setFeedback(`✓ ${newName} adicionado`);
        setNewSlug("");
        setNewName("");
        setNewPhoto("");
      } else setFeedback(`Erro: ${res.error}`);
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-12 px-4 bg-black/70 backdrop-blur-sm overflow-y-auto" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl rounded-[30px] border border-white/10 bg-[#08090b] shadow-[0_30px_100px_-40px_rgba(0,180,252,0.55)] mb-16 overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.06]">
          <div>
            <div className="font-stencil text-4xl tracking-wider text-white">CONFIGURAÇÕES</div>
            <div className="text-sm text-white/40 mt-0.5">Personalização operacional</div>
          </div>
          <button type="button" onClick={onClose} className="text-white/40 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Logo */}
          <section>
            <div className="font-stencil text-2xl tracking-wider text-white mb-3">LOGO</div>
            <div className="flex items-center gap-3">
              <input
                type="url"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                placeholder="https://... (URL da imagem do logo)"
                className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-ms-blue text-sm transition-colors"
              />
              {logoUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={logoUrl} alt="preview" className="h-10 w-auto rounded-lg border border-white/[0.08] bg-white/[0.04]" />
              )}
            </div>
            <p className="text-xs text-white/35 mt-2">URL pública. Hospedagem sugerida: Imgur, Cloudinary, ou Supabase Storage.</p>
          </section>

          {/* Lista clientes */}
          <section>
            <div className="font-stencil text-2xl tracking-wider text-white mb-3">CLIENTES</div>
            <textarea
              value={clientsText}
              onChange={(e) => setClientsText(e.target.value)}
              rows={6}
              placeholder="Um cliente por linha&#10;Casa do Churras&#10;Impera Imóveis&#10;..."
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-ms-blue text-sm font-mono transition-colors"
            />
            <button
              onClick={saveSettings}
              disabled={isPending}
              className="mt-3 inline-flex items-center gap-2 px-5 py-2.5 bg-ms-blue text-black font-semibold text-sm rounded-xl shadow-lg shadow-ms-blue/25 hover:bg-ms-blue-soft disabled:opacity-50 transition-all"
            >
              <Save className="w-4 h-4" />
              SALVAR LOGO + CLIENTES
            </button>
          </section>

          {/* Usuários */}
          <section>
            <div className="font-stencil text-2xl tracking-wider text-white mb-3">EQUIPE</div>
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.slug} className="flex items-center gap-3 bg-white/[0.04] border border-white/[0.08] p-3 rounded-2xl">
                  {editingPhotos[u.slug] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={editingPhotos[u.slug]} alt={u.display_name} className="w-12 h-12 rounded-full object-cover border-2 border-ms-blue/60" />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-ms-blue/15 border-2 border-white/[0.08] flex items-center justify-center text-ms-blue font-bold text-lg">
                      {u.display_name[0]}
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="font-semibold text-white">{u.display_name}</div>
                    <div className="text-xs text-white/40">@{u.slug}</div>
                  </div>
                  <input
                    type="url"
                    value={editingPhotos[u.slug] || ""}
                    onChange={(e) => setEditingPhotos({ ...editingPhotos, [u.slug]: e.target.value })}
                    placeholder="URL da foto"
                    className="flex-1 bg-black/20 border border-white/[0.08] rounded-xl px-3 py-2 text-white placeholder:text-white/25 focus:outline-none focus:border-ms-blue text-xs transition-colors"
                  />
                  <button
                    onClick={() => saveUserPhoto(u.slug)}
                    disabled={isPending}
                    className="px-3 py-2 text-xs font-semibold border border-ms-blue/40 text-ms-blue hover:bg-ms-blue/10 disabled:opacity-50 rounded-xl transition-all"
                  >
                    Salvar
                  </button>
                </div>
              ))}
            </div>

            {/* Adicionar novo */}
            <div className="mt-4 p-4 border border-dashed border-white/[0.14] rounded-2xl bg-white/[0.025]">
              <div className="text-xs uppercase tracking-wider text-white/50 mb-2 font-semibold">Adicionar membro</div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                <input
                  type="text"
                  value={newSlug}
                  onChange={(e) => setNewSlug(e.target.value)}
                  placeholder="slug (ex: lucas)"
                  className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-white placeholder:text-white/25 text-xs focus:outline-none focus:border-ms-blue transition-colors"
                />
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Nome"
                  className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-white placeholder:text-white/25 text-xs focus:outline-none focus:border-ms-blue transition-colors"
                />
                <input
                  type="url"
                  value={newPhoto}
                  onChange={(e) => setNewPhoto(e.target.value)}
                  placeholder="URL foto (opcional)"
                  className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-white placeholder:text-white/25 text-xs focus:outline-none focus:border-ms-blue transition-colors"
                />
              </div>
              <button
                onClick={addUser}
                disabled={isPending}
                className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-white/[0.04] border border-ms-blue/40 text-ms-blue text-xs font-semibold hover:bg-ms-blue/10 disabled:opacity-50 rounded-xl transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                Adicionar
              </button>
            </div>
          </section>

          {feedback && (
            <div className={`text-sm px-3 py-2 rounded-xl border ${feedback.startsWith("✓") ? "text-ms-blue border-ms-blue/40 bg-ms-blue/10" : "text-ms-blue border-ms-blue/40 bg-ms-blue/10"}`}>
              {feedback}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
