import type { MenuGroup } from "@/data/menu";
import { GROUP_LABELS, type Lang } from "@/i18n/config";

export function resolveActiveGroupId(groups: MenuGroup[], selectedGroupId: string): string {
  if (groups.some((group) => group.id === selectedGroupId)) {
    return selectedGroupId;
  }

  return groups[0]?.id ?? "";
}

export function resolveMenuGroupLabel(group: MenuGroup, lang: Lang): string {
  return GROUP_LABELS[group.id]?.[lang] ?? group.label ?? group.id;
}
