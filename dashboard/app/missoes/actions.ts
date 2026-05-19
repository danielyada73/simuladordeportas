"use server";

import { revalidatePath } from "next/cache";
import { missionsApi } from "@/lib/missions-api";
import type { MissionPriority, MissionKind, MissionStatus } from "@/lib/missions-types";

export type CreateMissionInput = {
  name: string;
  client?: string;
  responsible_slug: string;
  priority: MissionPriority;
  kind: MissionKind;
  due_date: string;
  notes?: string;
  created_by_slug?: string;
};

export async function createMissionAction(input: CreateMissionInput) {
  try {
    const created = await missionsApi.create(input);
    revalidatePath("/missoes");
    return { ok: true as const, mission: created };
  } catch (e) {
    return { ok: false as const, error: e instanceof Error ? e.message : "Erro" };
  }
}

export async function updateMissionStatusAction(id: string, status: MissionStatus) {
  try {
    const updated = await missionsApi.patch(id, { status });
    revalidatePath("/missoes");
    return { ok: true as const, mission: updated };
  } catch (e) {
    return { ok: false as const, error: e instanceof Error ? e.message : "Erro" };
  }
}

export async function deleteMissionAction(id: string) {
  try {
    await missionsApi.remove(id);
    revalidatePath("/missoes");
    return { ok: true as const };
  } catch (e) {
    return { ok: false as const, error: e instanceof Error ? e.message : "Erro" };
  }
}

export async function updateSettingsAction(payload: { logo_url?: string; client_options?: string[] }) {
  try {
    const updated = await missionsApi.patchSettings(payload);
    revalidatePath("/missoes");
    return { ok: true as const, settings: updated };
  } catch (e) {
    return { ok: false as const, error: e instanceof Error ? e.message : "Erro" };
  }
}

export async function upsertUserAction(payload: {
  slug: string;
  display_name: string;
  photo_url?: string;
  accent_color?: string;
}) {
  try {
    await missionsApi.upsertUser(payload);
    revalidatePath("/missoes");
    return { ok: true as const };
  } catch (e) {
    return { ok: false as const, error: e instanceof Error ? e.message : "Erro" };
  }
}
