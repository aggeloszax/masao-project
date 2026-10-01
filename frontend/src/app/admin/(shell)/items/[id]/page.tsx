import { notFound } from "next/navigation";
import { ItemEditor } from "@/components/admin/ItemEditor";

export default async function AdminItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const itemId = Number(id);
  if (!Number.isInteger(itemId) || itemId <= 0) notFound();

  return <ItemEditor itemId={itemId} />;
}
