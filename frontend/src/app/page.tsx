import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { parseTableNumber } from "@/lib/table-context";

export const metadata: Metadata = {
  title: "Masao · Asian Fusion Lounge",
  description:
    "Discover Masao Asian Fusion Lounge — sushi, bao, cocktails and shisha, made for sharing.",
  alternates: { canonical: "/" },
};

type HomeProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;
  const rawTable = firstValue(params.table ?? params.table_number ?? params.t);
  const tableNumber = parseTableNumber(rawTable);

  // Keep existing table QR codes working after moving the menu to /menu.
  if (tableNumber !== null) redirect(`/menu?table=${tableNumber}`);

  return (
    <main className="relative isolate flex min-h-svh flex-col overflow-hidden bg-[#f6f1e8] text-[#17130f]">
      <div aria-hidden="true" className="absolute -right-28 -top-28 h-80 w-80 rounded-full border border-[#722f37]/15" />
      <div aria-hidden="true" className="absolute -bottom-44 -left-36 h-96 w-96 rounded-full bg-[#722f37]/8" />

      <nav className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-7 sm:px-10">
        <span className="font-serif text-xl font-semibold tracking-[0.18em]">MASAO</span>
        <Link href="/menu" className="text-xs font-semibold uppercase tracking-[0.22em] text-[#722f37] transition-opacity hover:opacity-65">
          Menu
        </Link>
      </nav>

      <section className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 items-center px-6 py-14 sm:px-10 sm:py-20">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.34em] text-[#8b0000]">Asian Fusion Lounge</p>
          <h1 className="mt-7 font-serif text-6xl leading-[0.94] tracking-[-0.045em] sm:text-8xl lg:text-9xl">
            Made to share.
            <br />
            Made to stay.
          </h1>
          <p className="mt-8 max-w-xl text-base leading-7 text-[#625b53] sm:text-lg">
            Sushi, bao, cocktails and shisha in one contemporary Asian fusion experience.
          </p>

          <div className="mt-10 flex flex-wrap gap-3">
            <Link href="/menu" className="inline-flex min-h-12 items-center justify-center rounded-full bg-[#722f37] px-7 text-sm font-semibold text-white transition-transform hover:-translate-y-0.5">
              Explore the menu
            </Link>
            <span className="inline-flex min-h-12 items-center rounded-full border border-[#17130f]/15 px-6 text-xs uppercase tracking-[0.18em] text-[#625b53]">
              6 languages
            </span>
          </div>
        </div>
      </section>

      <footer className="relative z-10 mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 border-t border-[#17130f]/10 px-6 py-6 text-[11px] uppercase tracking-[0.2em] text-[#716960] sm:px-10">
        <span>Masao · Asian Fusion Lounge</span>
        <span>Sushi · Bao · Cocktails · Shisha</span>
      </footer>
    </main>
  );
}

function firstValue(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}
