import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Πολιτική Απορρήτου",
  description: "Πολιτική απορρήτου του ψηφιακού μενού και του AI assistant του Masao.",
  robots: { index: false, follow: true },
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto min-h-screen w-full max-w-2xl bg-background px-6 py-10 text-foreground">
      <Link href="/" className="text-sm font-medium text-accent underline underline-offset-4">
        ← Επιστροφή στο μενού
      </Link>

      <article className="mt-8 space-y-8">
        <header>
          <p className="font-serif text-xs uppercase tracking-[0.35em] text-accent-soft">Masao</p>
          <h1 className="mt-3 font-serif text-4xl">Πολιτική Απορρήτου</h1>
          <p className="mt-3 text-sm text-muted">Τελευταία ενημέρωση: 10 Αυγούστου 2026</p>
        </header>

        <Notice title="Με λίγα λόγια">
          Μπορείτε να χρησιμοποιήσετε το μενού χωρίς λογαριασμό. Το AI chat χρησιμοποιεί ένα
          τυχαίο αναγνωριστικό συσκευής και διατηρεί τα μηνύματα έως 30 ημέρες. Μην καταχωρείτε
          όνομα, τηλέφωνο ή άλλα στοιχεία που σας ταυτοποιούν.
        </Notice>

        <Section title="1. Υπεύθυνος επεξεργασίας">
          Υπεύθυνη για τη λειτουργία της υπηρεσίας είναι η επιχείρηση Masao Asian Fusion Lounge.
          Για ερωτήματα απορρήτου ή αιτήματα σχετικά με τα δεδομένα σας, επικοινωνήστε με το
          κατάστημα ή απευθυνθείτε στο προσωπικό του Masao.
        </Section>

        <Section title="2. Ποια δεδομένα χρησιμοποιούνται">
          <ul className="list-disc space-y-2 ps-5">
            <li>Τα μηνύματα που επιλέγετε να στείλετε στο AI chat.</li>
            <li>Η επιλεγμένη γλώσσα και ένα τυχαίο, ανώνυμο αναγνωριστικό συσκευής.</li>
            <li>Τυχόν πληροφορίες αλλεργιών που επιλέγετε να αναφέρετε.</li>
            <li>Βασικά τεχνικά δεδομένα ασφαλείας και στοιχεία αιτημάτων.</li>
          </ul>
          <p className="mt-3">
            Η λίστα πιάτων και οι σημειώσεις της επιλογής σας αποθηκεύονται τοπικά στη συσκευή σας.
          </p>
        </Section>

        <Section title="3. Γιατί χρησιμοποιούνται">
          Τα δεδομένα χρησιμοποιούνται μόνο για να λειτουργεί το ψηφιακό μενού, να απαντά το AI
          assistant, να θυμάται τις επιλογές στη συσκευή σας, να εμφανίζει σχετικές προειδοποιήσεις
          και να προστατεύεται η υπηρεσία από κατάχρηση και τεχνικά προβλήματα.
        </Section>

        <Section title="4. AI και πάροχοι υπηρεσιών">
          Τα μηνύματα του chat αποστέλλονται σε υπηρεσία τεχνητής νοημοσύνης για τη δημιουργία
          απάντησης. Για τη φιλοξενία και λειτουργία της εφαρμογής χρησιμοποιούνται εξωτερικοί
          πάροχοι υποδομής, βάσης δεδομένων και προστασίας από κατάχρηση. Οι πάροχοι ενεργούν για
          την παροχή της υπηρεσίας σύμφωνα με τους όρους και τις υποχρεώσεις προστασίας δεδομένων
          που τους διέπουν.
        </Section>

        <Section title="5. Χρόνος διατήρησης">
          Οι συνομιλίες διατηρούνται έως 30 ημέρες και στη συνέχεια διαγράφονται. Οι τοπικές
          επιλογές μενού παραμένουν στη συσκευή σας μέχρι να τις καθαρίσετε ή να διαγράψετε τα
          δεδομένα του browser.
        </Section>

        <Section title="6. Τα δικαιώματά σας">
          Ανάλογα με την περίπτωση, μπορείτε να ζητήσετε ενημέρωση, πρόσβαση, διόρθωση, διαγραφή,
          περιορισμό ή να αντιταχθείτε στην επεξεργασία. Μπορείτε επίσης να απευθυνθείτε στην
          αρμόδια αρχή προστασίας δεδομένων. Επειδή η υπηρεσία δεν ζητά λογαριασμό ή στοιχεία
          ταυτότητας, ενδέχεται να χρειαστούν τεχνικές πληροφορίες από τη συσκευή σας για να
          εντοπιστεί ένα συγκεκριμένο αίτημα.
        </Section>

        <Notice title="Σημαντικό για αλλεργίες">
          Οι απαντήσεις του AI και οι πληροφορίες του ψηφιακού μενού μπορεί να είναι ελλιπείς ή να
          περιέχουν λάθη και δεν αποτελούν εγγύηση ασφάλειας. Για κάθε αλλεργία ή δυσανεξία,
          ενημερώστε και επιβεβαιώστε πάντα με το προσωπικό πριν παραγγείλετε. Υπάρχει πιθανότητα
          διασταυρούμενης επιμόλυνσης.
        </Notice>

        <section className="border-t border-hairline pt-8" lang="en">
          <h2 className="font-serif text-2xl">English summary</h2>
          <p className="mt-3 text-sm leading-7 text-muted">
            You may browse the menu without an account. The AI chat uses a random device identifier
            and retains messages for up to 30 days. Messages are processed by an AI service to
            generate replies. Do not enter your name, phone number or other identifying details.
            AI and allergen information may be incomplete; always inform and confirm with restaurant
            staff before ordering, as cross-contamination may occur. Contact the Masao venue or its
            staff for privacy requests.
          </p>
        </section>
      </article>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="font-serif text-2xl">{title}</h2>
      <div className="mt-3 text-sm leading-7 text-muted">{children}</div>
    </section>
  );
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-hairline bg-surface p-5">
      <h2 className="font-semibold text-accent">{title}</h2>
      <p className="mt-2 text-sm leading-7 text-muted">{children}</p>
    </section>
  );
}
