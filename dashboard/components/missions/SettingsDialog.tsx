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
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-camo-deep/80 backdrop-blur-sm overflow-y-auto" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-camo-base border border-camo-cyan/30 rounded-sm shadow-tactical mb-16"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-camo-line">
          <div>
            <div className="font-stencil text-3xl tracking-widest text-camo-cyan">CONFIGURAÇÕES</div>
            <div className="text-xs text-camo-cyan/50 uppercase tracking-wider">Personalização operacional</div>
          </div>
          <button type="button" onClick={onClose} className="text-camo-cyan/60 hover:text-camo-cyan">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Logo */}
          <section>
            <div className="font-stencil text-xl tracking-wider text-camo-cyan mb-3">LOGO</div>
            <div className="flex items-center gap-3">
              <input
                type="url"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                placeholder="https://... (URL da imagem do logo)"
                className="flex-1 bg-camo-deep border border-camo-line rounded-sm px-3 py-2 text-text placeholder:text-camo-cyan/30 focus:outline-none focus:border-camo-cyan text-sm"
              />
              {logoUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={logoUrl} alt="preview" className="h-10 w-auto border border-camo-line bg-camo-deep" />
              )}
            </div>
            <p className="text-xs text-camo-cyan/40 mt-2">URL pública. Hospedagem sugerida: Imgur, Cloudinary, ou Supabase Storage.</p>
          </section>

          {/* Lista clientes */}
          <section>
            <div className="font-stencil text-xl tracking-wider text-camo-cyan mb-3">CLIENTES (sugestões no formulário)</div>
            <textarea
              value={clientsText}
              onChange={(e) => setClientsText(e.target.value)}
              rows={6}
              placeholder="Um cliente por linha&#10;Casa do Churras&#10;Impera Imóveis&#10;..."
              className="w-full bg-camo-deep border border-camo-line rounded-sm px-3 py-2 text-text placeholder:text-camo-cyan/30 focus:outline-none focus:border-camo-cyan text-sm font-mono"
            />
            <button
              onClick={saveSettings}
              disabled={isPending}
              className="mt-3 flex items-center gap-2 px-4 py-2 bg-camo-cyan text-camo-deep font-stencil tracking-widest text-sm rounded-sm hover:brightness-110 disabled:opacity-50 transition-all"
            >
              <Save className="w-4 h-4" />
              SALVAR LOGO + CLIENTES
            </button>
          </section>

          {/* Usuários */}
          <section>
            <div className="font-stencil text-xl tracking-wider text-camo-cyan mb-3">EQUIPE</div>
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.slug} className="flex items-center gap-3 bg-camo-deep/60 border border-camo-line p-3 rounded-sm">
                  {editingPhotos[u.slug] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={editingPhotos[u.slug]} alt={u.display_name} className="w-12 h-12 rounded-full object-cover border-2 border-camo-cyan/50" />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-camo-mid border-2 border-camo-line flex items-center justify-center text-camo-cyan font-bold text-lg">
                      {u.display_name[0]}
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="font-stencil text-lg tracking-wider text-camo-cyan">{u.display_name}</div>
                    <div className="text-xs text-camo-cyan/50">@{u.slug}</div>
                  </div>
                  <input
                    type="url"
                    value={editingPhotos[u.slug] || ""}
                    onChange={(e) => setEditingPhotos({ ...editingPhotos, [u.slug]: e.target.value })}
                    placeholder="URL da foto"
                    className="flex-1 bg-camo-deep border border-camo-line rounded-sm px-2 py-1.5 text-text placeholder:text-camo-cyan/30 focus:outline-none focus:border-camo-cyan text-xs"
                  />
                  <button
                    onClick={() => saveUserPhoto(u.slug)}
                    disabled={isPending}
                    className="px-3 py-1.5 text-xs uppercase tracking-wider border border-camo-cyan/40 text-camo-cyan hover:bg-camo-mid disabled:opacity-50 rounded-sm transition-all"
                  >
                    Salvar
                  </button>
                </div>
              ))}
            </div>

            {/* Adicionar novo */}
            <div className="mt-4 p-3 border border-dashed border-camo-cyan/30 rounded-sm bg-camo-deep/30">
              <div className="text-xs uppercase tracking-wider text-camo-cyan/70 mb-2 font-semibold">Adicionar membro</div>
              <div className="grid grid-cols-3 gap-2">
                <input
                  type="text"
                  value={newSlug}
                  onChange={(e) => setNewSlug(e.target.value)}
                  placeholder="slug (ex: lucas)"
                  className="bg-camo-deep border border-camo-line rounded-sm px-2 py-1.5 text-text placeholder:text-camo-cyan/30 text-xs focus:outline-none focus:border-camo-cyan"
                />
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Nome"
                  className="bg-camo-deep border border-camo-line rounded-sm px-2 py-1.5 text-text placeholder:text-camo-cyan/30 text-xs focus:outline-none focus:border-camo-cyan"
                />
                <input
                  type="url"
                  value={newPhoto}
                  onChange={(e) => setNewPhoto(e.target.value)}
                  placeholder="URL foto (opcional)"
                  className="bg-camo-deep border border-camo-line rounded-sm px-2 py-1.5 text-text placeholder:text-camo-cyan/30 text-xs focus:outline-none focus:border-camo-cyan"
                />
              </div>
              <button
                onClick={addUser}
                disabled={isPending}
                className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-camo-mid border border-camo-cyan/40 text-camo-cyan text-xs uppercase tracking-wider hover:bg-camo-light disabled:opacity-50 rounded-sm transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                Adicionar
              </button>
            </div>
          </section>

          {feedback && (
            <div className={`text-sm px-3 py-2 rounded-sm border ${feedback.startsWith("✓") ? "text-low border-low/40 bg-low/10" : "text-urgent border-urgent/40 bg-urgent/10"}`}>
              {feedback}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
