"use client";

import Link from "next/link";
import { useLanguage } from "@/i18n/LanguageContext";
import type { Lang } from "@/i18n/config";

type PrivacyCopy = {
  back: string; title: string; updated: string; summaryTitle: string; summary: string;
  sections: { title: string; body: string; items?: string[]; after?: string }[];
  allergyTitle: string; allergy: string;
};

const COPY: Record<Lang, PrivacyCopy> = {
  el: {
    back: "← Επιστροφή στο μενού", title: "Πολιτική Απορρήτου", updated: "Τελευταία ενημέρωση: 12 Αυγούστου 2026",
    summaryTitle: "Με λίγα λόγια", summary: "Μπορείτε να χρησιμοποιήσετε το μενού χωρίς λογαριασμό. Το AI chat χρησιμοποιεί ένα τυχαίο αναγνωριστικό συσκευής και διατηρεί τα μηνύματα έως 30 ημέρες. Μην καταχωρείτε όνομα, τηλέφωνο ή άλλα στοιχεία που σας ταυτοποιούν.",
    sections: [
      { title: "1. Υπεύθυνος επεξεργασίας", body: "Υπεύθυνη για τη λειτουργία της υπηρεσίας είναι η επιχείρηση Masao Asian Fusion Lounge. Για ερωτήματα απορρήτου ή αιτήματα σχετικά με τα δεδομένα σας, επικοινωνήστε με το κατάστημα ή το προσωπικό του Masao." },
      { title: "2. Ποια δεδομένα χρησιμοποιούνται", body: "Η υπηρεσία χρησιμοποιεί:", items: ["Τα μηνύματα που επιλέγετε να στείλετε στο AI chat.", "Την επιλεγμένη γλώσσα και ένα τυχαίο, ψευδωνυμοποιημένο αναγνωριστικό συσκευής.", "Τυχόν πληροφορίες αλλεργιών που επιλέγετε να δηλώσετε.", "Βασικά τεχνικά δεδομένα ασφάλειας και στοιχεία αιτημάτων."], after: "Η λίστα πιάτων και οι σημειώσεις της επιλογής σας αποθηκεύονται τοπικά στη συσκευή σας." },
      { title: "3. Γιατί χρησιμοποιούνται", body: "Τα δεδομένα χρησιμοποιούνται για να λειτουργεί το ψηφιακό μενού, να απαντά ο AI assistant, να διατηρεί το ιστορικό της συνομιλίας στη συσκευή, να εμφανίζει σχετικές προειδοποιήσεις και να προστατεύεται η υπηρεσία από κατάχρηση και τεχνικά προβλήματα." },
      { title: "4. AI και πάροχοι υπηρεσιών", body: "Τα μηνύματα του chat αποστέλλονται σε υπηρεσία τεχνητής νοημοσύνης για τη δημιουργία απάντησης. Εξωτερικοί πάροχοι υποδομής, βάσης δεδομένων και προστασίας από κατάχρηση χρησιμοποιούνται για τη λειτουργία της εφαρμογής, σύμφωνα με τους όρους και τις υποχρεώσεις προστασίας δεδομένων που τους διέπουν." },
      { title: "5. Χρόνος διατήρησης", body: "Οι συνομιλίες διατηρούνται έως 30 ημέρες και στη συνέχεια διαγράφονται. Οι τοπικές επιλογές μενού ισχύουν μόνο για την τρέχουσα επίσκεψη και διαγράφονται όταν κλείσει η καρτέλα του browser." },
      { title: "6. Τα δικαιώματά σας", body: "Ανάλογα με την περίπτωση, μπορείτε να ζητήσετε ενημέρωση, πρόσβαση, διόρθωση, διαγραφή, περιορισμό ή να αντιταχθείτε στην επεξεργασία. Μπορείτε επίσης να απευθυνθείτε στην αρμόδια αρχή προστασίας δεδομένων. Επειδή η υπηρεσία δεν ζητά λογαριασμό ή στοιχεία ταυτότητας, μπορεί να χρειαστούν τεχνικές πληροφορίες από τη συσκευή σας για τον εντοπισμό ενός αιτήματος." },
    ], allergyTitle: "Σημαντικό για αλλεργίες", allergy: "Οι απαντήσεις του AI και οι πληροφορίες του ψηφιακού μενού μπορεί να είναι ελλιπείς ή λανθασμένες και δεν αποτελούν εγγύηση ασφάλειας. Για κάθε αλλεργία ή δυσανεξία, ενημερώστε και επιβεβαιώστε πάντα με το προσωπικό πριν παραγγείλετε. Υπάρχει πιθανότητα διασταυρούμενης επιμόλυνσης.",
  },
  en: {
    back: "← Back to menu", title: "Privacy Policy", updated: "Last updated: 12 August 2026",
    summaryTitle: "In brief", summary: "You can use the menu without an account. The AI chat uses a random device identifier and retains messages for up to 30 days. Do not enter your name, phone number or other identifying details.",
    sections: [
      { title: "1. Data controller", body: "Masao Asian Fusion Lounge is responsible for operating this service. For privacy questions or requests concerning your data, contact the Masao venue or its staff." },
      { title: "2. Data we use", body: "The service uses:", items: ["Messages you choose to send to the AI chat.", "Your selected language and a random, pseudonymous device identifier.", "Any allergy information you choose to provide.", "Basic security and request-related technical data."], after: "Your selected dishes and notes are stored locally on your device." },
      { title: "3. Why we use it", body: "Data is used to operate the digital menu, provide AI assistant replies, retain conversation history for the device, show relevant warnings and protect the service from abuse and technical problems." },
      { title: "4. AI and service providers", body: "Chat messages are sent to an artificial intelligence service to generate a reply. External infrastructure, database and abuse-prevention providers are used to operate the application under their applicable terms and data-protection obligations." },
      { title: "5. Retention", body: "Conversations are retained for up to 30 days and are then deleted. Local menu selections apply only to your current visit and are cleared when the browser tab is closed." },
      { title: "6. Your rights", body: "Depending on the circumstances, you may request information, access, correction, erasure or restriction, or object to processing. You may also complain to the competent data-protection authority. Because the service does not request an account or identity details, technical information from your device may be needed to locate a request." },
    ], allergyTitle: "Important allergy information", allergy: "AI answers and digital-menu information may be incomplete or inaccurate and are not a guarantee of safety. For every allergy or intolerance, always inform and confirm with staff before ordering. Cross-contamination may occur.",
  },
  de: {
    back: "← Zurück zur Speisekarte", title: "Datenschutzerklärung", updated: "Zuletzt aktualisiert: 12. August 2026",
    summaryTitle: "Kurz gesagt", summary: "Sie können die Speisekarte ohne Konto nutzen. Der KI-Chat verwendet eine zufällige Gerätekennung und speichert Nachrichten bis zu 30 Tage. Geben Sie keinen Namen, keine Telefonnummer oder andere identifizierende Angaben ein.",
    sections: [
      { title: "1. Verantwortlicher", body: "Für den Betrieb dieses Dienstes ist die Masao Asian Fusion Lounge verantwortlich. Bei Datenschutzfragen oder Anfragen zu Ihren Daten wenden Sie sich an das Masao-Lokal oder dessen Personal." },
      { title: "2. Verwendete Daten", body: "Der Dienst verwendet:", items: ["Nachrichten, die Sie an den KI-Chat senden.", "Ihre gewählte Sprache und eine zufällige, pseudonyme Gerätekennung.", "Allergieangaben, die Sie freiwillig machen.", "Grundlegende Sicherheits- und technische Anfragedaten."], after: "Ihre ausgewählten Gerichte und Notizen werden lokal auf Ihrem Gerät gespeichert." },
      { title: "3. Verwendungszwecke", body: "Die Daten dienen dem Betrieb der digitalen Speisekarte, den Antworten des KI-Assistenten, dem Gesprächsverlauf auf dem Gerät, relevanten Warnungen sowie dem Schutz vor Missbrauch und technischen Problemen." },
      { title: "4. KI und Dienstleister", body: "Chat-Nachrichten werden zur Erstellung einer Antwort an einen KI-Dienst gesendet. Externe Anbieter für Infrastruktur, Datenbank und Missbrauchsschutz unterstützen den Betrieb nach ihren geltenden Datenschutzpflichten." },
      { title: "5. Speicherdauer", body: "Unterhaltungen werden bis zu 30 Tage gespeichert und anschließend gelöscht. Lokale Menüauswahlen gelten nur für den aktuellen Besuch und werden beim Schließen des Browser-Tabs gelöscht." },
      { title: "6. Ihre Rechte", body: "Je nach Fall können Sie Auskunft, Zugang, Berichtigung, Löschung oder Einschränkung verlangen oder der Verarbeitung widersprechen. Sie können sich auch bei der zuständigen Datenschutzbehörde beschweren. Zur Zuordnung einer Anfrage können technische Geräteinformationen nötig sein." },
    ], allergyTitle: "Wichtiger Hinweis zu Allergien", allergy: "KI-Antworten und Angaben im digitalen Menü können unvollständig oder fehlerhaft sein und garantieren keine Sicherheit. Informieren Sie bei Allergien oder Unverträglichkeiten immer das Personal und lassen Sie die Angaben vor der Bestellung bestätigen. Kreuzkontamination ist möglich.",
  },
  it: {
    back: "← Torna al menu", title: "Informativa sulla privacy", updated: "Ultimo aggiornamento: 12 agosto 2026",
    summaryTitle: "In breve", summary: "Puoi usare il menu senza un account. La chat AI utilizza un identificativo casuale del dispositivo e conserva i messaggi fino a 30 giorni. Non inserire nome, telefono o altri dati identificativi.",
    sections: [
      { title: "1. Titolare del trattamento", body: "Masao Asian Fusion Lounge è responsabile del funzionamento del servizio. Per domande sulla privacy o richieste relative ai dati, contatta il locale Masao o il personale." },
      { title: "2. Dati utilizzati", body: "Il servizio utilizza:", items: ["I messaggi che scegli di inviare alla chat AI.", "La lingua selezionata e un identificativo casuale e pseudonimo del dispositivo.", "Le informazioni sulle allergie che scegli di fornire.", "Dati tecnici essenziali di sicurezza e delle richieste."], after: "I piatti selezionati e le note sono memorizzati localmente sul dispositivo." },
      { title: "3. Finalità", body: "I dati servono a far funzionare il menu digitale, fornire le risposte dell’assistente AI, conservare la cronologia per il dispositivo, mostrare avvisi pertinenti e proteggere il servizio da abusi e problemi tecnici." },
      { title: "4. AI e fornitori", body: "I messaggi della chat vengono inviati a un servizio di intelligenza artificiale per generare la risposta. Fornitori esterni di infrastruttura, database e prevenzione degli abusi supportano l’applicazione secondo i rispettivi obblighi di protezione dei dati." },
      { title: "5. Conservazione", body: "Le conversazioni sono conservate fino a 30 giorni e poi eliminate. Le selezioni locali valgono solo per la visita corrente e vengono cancellate alla chiusura della scheda del browser." },
      { title: "6. I tuoi diritti", body: "A seconda dei casi puoi chiedere informazioni, accesso, rettifica, cancellazione o limitazione, oppure opporti al trattamento. Puoi inoltre presentare reclamo all’autorità competente. Per individuare una richiesta potrebbero servire informazioni tecniche del dispositivo." },
    ], allergyTitle: "Informazioni importanti sulle allergie", allergy: "Le risposte AI e le informazioni del menu digitale possono essere incomplete o errate e non garantiscono la sicurezza. Per allergie o intolleranze, informa sempre il personale e chiedi conferma prima di ordinare. È possibile la contaminazione incrociata.",
  },
  sv: {
    back: "← Tillbaka till menyn", title: "Integritetspolicy", updated: "Senast uppdaterad: 12 augusti 2026",
    summaryTitle: "Kortfattat", summary: "Du kan använda menyn utan konto. AI-chatten använder en slumpmässig enhetsidentifierare och sparar meddelanden i upp till 30 dagar. Ange inte namn, telefonnummer eller andra identifierande uppgifter.",
    sections: [
      { title: "1. Personuppgiftsansvarig", body: "Masao Asian Fusion Lounge ansvarar för tjänsten. Kontakta Masao-restaurangen eller personalen vid integritetsfrågor eller begäranden om dina uppgifter." },
      { title: "2. Uppgifter som används", body: "Tjänsten använder:", items: ["Meddelanden du väljer att skicka till AI-chatten.", "Ditt valda språk och en slumpmässig, pseudonym enhetsidentifierare.", "Allergiinformation som du väljer att lämna.", "Grundläggande säkerhets- och tekniska förfrågningsuppgifter."], after: "Valda rätter och anteckningar lagras lokalt på din enhet." },
      { title: "3. Varför uppgifterna används", body: "Uppgifterna används för den digitala menyn, AI-assistentens svar, samtalshistorik för enheten, relevanta varningar och skydd mot missbruk och tekniska problem." },
      { title: "4. AI och tjänsteleverantörer", body: "Chattmeddelanden skickas till en AI-tjänst för att skapa svar. Externa leverantörer av infrastruktur, databas och missbruksskydd används enligt tillämpliga dataskyddsskyldigheter." },
      { title: "5. Lagringstid", body: "Samtal sparas i upp till 30 dagar och raderas sedan. Lokala menyval gäller endast ditt aktuella besök och rensas när webbläsarfliken stängs." },
      { title: "6. Dina rättigheter", body: "Beroende på omständigheterna kan du begära information, tillgång, rättelse, radering eller begränsning, eller invända mot behandlingen. Du kan också klaga hos behörig dataskyddsmyndighet. Teknisk enhetsinformation kan behövas för att hitta en begäran." },
    ], allergyTitle: "Viktig allergiinformation", allergy: "AI-svar och information i den digitala menyn kan vara ofullständiga eller felaktiga och garanterar inte säkerhet. Informera alltid personalen om allergier eller intoleranser och bekräfta före beställning. Korskontaminering kan förekomma.",
  },
  fr: {
    back: "← Retour au menu", title: "Politique de confidentialité", updated: "Dernière mise à jour : 12 août 2026",
    summaryTitle: "En bref", summary: "Vous pouvez utiliser le menu sans compte. Le chat IA utilise un identifiant aléatoire de l’appareil et conserve les messages jusqu’à 30 jours. N’indiquez pas votre nom, votre téléphone ni d’autres données permettant de vous identifier.",
    sections: [
      { title: "1. Responsable du traitement", body: "Masao Asian Fusion Lounge est responsable du fonctionnement de ce service. Pour toute question ou demande relative à vos données, contactez l’établissement Masao ou son personnel." },
      { title: "2. Données utilisées", body: "Le service utilise :", items: ["Les messages que vous choisissez d’envoyer au chat IA.", "La langue choisie et un identifiant aléatoire et pseudonyme de l’appareil.", "Les informations sur les allergies que vous choisissez de fournir.", "Des données techniques essentielles de sécurité et de requête."], after: "Vos plats sélectionnés et vos notes sont stockés localement sur votre appareil." },
      { title: "3. Finalités", body: "Les données servent au fonctionnement du menu numérique, aux réponses de l’assistant IA, à l’historique de la conversation sur l’appareil, aux avertissements pertinents et à la protection contre les abus et problèmes techniques." },
      { title: "4. IA et prestataires", body: "Les messages du chat sont envoyés à un service d’intelligence artificielle afin de générer une réponse. Des prestataires externes d’infrastructure, de base de données et de prévention des abus participent au fonctionnement selon leurs obligations de protection des données." },
      { title: "5. Conservation", body: "Les conversations sont conservées jusqu’à 30 jours puis supprimées. Les sélections locales ne valent que pour la visite en cours et sont effacées à la fermeture de l’onglet du navigateur." },
      { title: "6. Vos droits", body: "Selon les circonstances, vous pouvez demander information, accès, rectification, effacement ou limitation, ou vous opposer au traitement. Vous pouvez aussi saisir l’autorité compétente. Des informations techniques de l’appareil peuvent être nécessaires pour retrouver une demande." },
    ], allergyTitle: "Information importante sur les allergies", allergy: "Les réponses de l’IA et les informations du menu numérique peuvent être incomplètes ou erronées et ne garantissent pas la sécurité. Pour toute allergie ou intolérance, informez toujours le personnel et confirmez avant de commander. Une contamination croisée est possible.",
  },
  ru: {
    back: "← Вернуться в меню", title: "Политика конфиденциальности", updated: "Последнее обновление: 12 августа 2026 г.",
    summaryTitle: "Кратко", summary: "Меню можно использовать без учётной записи. ИИ-чат использует случайный идентификатор устройства и хранит сообщения до 30 дней. Не указывайте имя, телефон и другие идентифицирующие сведения.",
    sections: [
      { title: "1. Оператор данных", body: "За работу сервиса отвечает Masao Asian Fusion Lounge. По вопросам конфиденциальности или запросам о данных обратитесь в заведение Masao или к его сотрудникам." },
      { title: "2. Используемые данные", body: "Сервис использует:", items: ["Сообщения, которые вы отправляете в ИИ-чат.", "Выбранный язык и случайный псевдонимный идентификатор устройства.", "Сведения об аллергиях, которые вы решите указать.", "Основные технические данные безопасности и запросов."], after: "Выбранные блюда и заметки хранятся локально на вашем устройстве." },
      { title: "3. Цели использования", body: "Данные используются для работы цифрового меню, ответов ИИ-помощника, истории беседы на устройстве, соответствующих предупреждений и защиты сервиса от злоупотреблений и технических проблем." },
      { title: "4. ИИ и поставщики услуг", body: "Сообщения чата передаются сервису искусственного интеллекта для создания ответа. Внешние поставщики инфраструктуры, базы данных и защиты от злоупотреблений участвуют в работе приложения согласно применимым требованиям защиты данных." },
      { title: "5. Срок хранения", body: "Беседы хранятся до 30 дней, после чего удаляются. Локальные выбранные позиции действуют только для текущего визита и удаляются при закрытии вкладки браузера." },
      { title: "6. Ваши права", body: "В зависимости от обстоятельств вы можете запросить информацию, доступ, исправление, удаление или ограничение либо возразить против обработки. Вы также можете обратиться в компетентный надзорный орган. Для поиска запроса могут потребоваться технические сведения устройства." },
    ], allergyTitle: "Важная информация об аллергиях", allergy: "Ответы ИИ и сведения цифрового меню могут быть неполными или ошибочными и не гарантируют безопасность. При аллергии или непереносимости всегда сообщайте персоналу и уточняйте информацию до заказа. Возможна перекрёстная контаминация.",
  },
  he: {
    back: "חזרה לתפריט →", title: "מדיניות פרטיות", updated: "עדכון אחרון: 12 באוגוסט 2026",
    summaryTitle: "בקצרה", summary: "ניתן להשתמש בתפריט ללא חשבון. צ'אט ה-AI משתמש במזהה מכשיר אקראי ושומר הודעות עד 30 יום. אין להזין שם, מספר טלפון או פרטים מזהים אחרים.",
    sections: [
      { title: "1. בעל השליטה במידע", body: "Masao Asian Fusion Lounge אחראית להפעלת השירות. לשאלות פרטיות או לבקשות הנוגעות למידע שלכם, פנו למסעדת Masao או לצוות שלה." },
      { title: "2. מידע בשימוש", body: "השירות משתמש ב:", items: ["הודעות שתבחרו לשלוח לצ'אט ה-AI.", "השפה שנבחרה ומזהה מכשיר אקראי ופסאודונימי.", "מידע על אלרגיות שתבחרו למסור.", "נתוני אבטחה ונתונים טכניים בסיסיים של בקשות."], after: "המנות וההערות שבחרתם נשמרות מקומית במכשיר." },
      { title: "3. מטרות השימוש", body: "המידע משמש להפעלת התפריט הדיגיטלי, למענה של עוזר ה-AI, לשמירת היסטוריית השיחה במכשיר, להצגת אזהרות רלוונטיות ולהגנה מפני שימוש לרעה ובעיות טכניות." },
      { title: "4. AI וספקי שירות", body: "הודעות הצ'אט נשלחות לשירות בינה מלאכותית לצורך יצירת תשובה. ספקים חיצוניים של תשתית, מסד נתונים והגנה מפני שימוש לרעה מסייעים בהפעלת היישום בהתאם לחובות הגנת המידע החלות עליהם." },
      { title: "5. תקופת שמירה", body: "שיחות נשמרות עד 30 יום ולאחר מכן נמחקות. בחירות מקומיות תקפות רק לביקור הנוכחי ונמחקות עם סגירת כרטיסיית הדפדפן." },
      { title: "6. הזכויות שלכם", body: "בהתאם לנסיבות ניתן לבקש מידע, גישה, תיקון, מחיקה או הגבלה, או להתנגד לעיבוד. ניתן גם לפנות לרשות המוסמכת להגנת מידע. ייתכן שיידרש מידע טכני מהמכשיר כדי לאתר בקשה." },
    ], allergyTitle: "מידע חשוב על אלרגיות", allergy: "תשובות ה-AI ומידע התפריט הדיגיטלי עלולים להיות חלקיים או שגויים ואינם מבטיחים בטיחות. בכל אלרגיה או אי-סבילות יש ליידע תמיד את הצוות ולאשר לפני ההזמנה. תיתכן זיהום צולב.",
  },
  tr: {
    back: "← Menüye dön", title: "Gizlilik Politikası", updated: "Son güncelleme: 12 Ağustos 2026",
    summaryTitle: "Kısaca", summary: "Menüyü hesap açmadan kullanabilirsiniz. Yapay zekâ sohbeti rastgele bir cihaz tanımlayıcısı kullanır ve mesajları 30 güne kadar saklar. Adınızı, telefon numaranızı veya diğer kimlik bilgilerinizi yazmayın.",
    sections: [
      { title: "1. Veri sorumlusu", body: "Bu hizmetin işletilmesinden Masao Asian Fusion Lounge sorumludur. Gizlilikle ilgili sorularınız veya verilerinize ilişkin talepleriniz için Masao mekânına veya personeline başvurun." },
      { title: "2. Kullanılan veriler", body: "Hizmet şunları kullanır:", items: ["Yapay zekâ sohbetine göndermeyi seçtiğiniz mesajlar.", "Seçtiğiniz dil ve rastgele, takma adlı bir cihaz tanımlayıcısı.", "Vermeyi seçtiğiniz alerji bilgileri.", "Temel güvenlik ve istek kaynaklı teknik veriler."], after: "Seçtiğiniz yemekler ve notlar cihazınızda yerel olarak saklanır." },
      { title: "3. Kullanım amaçları", body: "Veriler; dijital menünün çalışması, yapay zekâ asistanının yanıt vermesi, cihazdaki sohbet geçmişinin tutulması, ilgili uyarıların gösterilmesi ve hizmetin kötüye kullanım ile teknik sorunlardan korunması için kullanılır." },
      { title: "4. Yapay zekâ ve hizmet sağlayıcılar", body: "Sohbet mesajları, yanıt oluşturmak için bir yapay zekâ hizmetine gönderilir. Uygulamanın işletilmesinde altyapı, veritabanı ve kötüye kullanım koruması sağlayan dış sağlayıcılar, tabi oldukları veri koruma yükümlülükleri çerçevesinde kullanılır." },
      { title: "5. Saklama süresi", body: "Konuşmalar 30 güne kadar saklanır ve ardından silinir. Yerel menü seçimleri yalnızca mevcut ziyaretiniz için geçerlidir ve tarayıcı sekmesi kapatıldığında silinir." },
      { title: "6. Haklarınız", body: "Duruma göre bilgi, erişim, düzeltme, silme veya kısıtlama talep edebilir ya da işlemeye itiraz edebilirsiniz. Yetkili veri koruma otoritesine de şikâyette bulunabilirsiniz. Hizmet hesap veya kimlik bilgisi istemediği için, bir talebin bulunabilmesi amacıyla cihazınızdan teknik bilgiler gerekebilir." },
    ], allergyTitle: "Alerjiler hakkında önemli bilgi", allergy: "Yapay zekâ yanıtları ve dijital menü bilgileri eksik veya hatalı olabilir ve güvenlik garantisi değildir. Her alerji veya intolerans için sipariş vermeden önce personeli mutlaka bilgilendirin ve teyit edin. Çapraz bulaşma olasılığı vardır.",
  },
};

export function PrivacyContent() {
  const { lang, rtl } = useLanguage();
  const copy = COPY[lang];
  return (
    <main dir={rtl ? "rtl" : "ltr"} className="mx-auto min-h-screen w-full max-w-2xl bg-background px-6 py-10 text-foreground">
      <Link href="/" className="text-sm font-medium text-accent underline underline-offset-4">{copy.back}</Link>
      <article className="mt-8 space-y-8">
        <header><p className="font-serif text-xs uppercase tracking-[0.35em] text-accent-soft">Masao</p><h1 className="mt-3 font-serif text-4xl">{copy.title}</h1><p className="mt-3 text-sm text-muted">{copy.updated}</p></header>
        <Notice title={copy.summaryTitle}>{copy.summary}</Notice>
        {copy.sections.map((section) => <Section key={section.title} {...section} />)}
        <Notice title={copy.allergyTitle}>{copy.allergy}</Notice>
      </article>
    </main>
  );
}

function Section({ title, body, items, after }: PrivacyCopy["sections"][number]) {
  return <section><h2 className="font-serif text-2xl">{title}</h2><div className="mt-3 text-sm leading-7 text-muted"><p>{body}</p>{items && <ul className="mt-2 list-disc space-y-2 ps-5">{items.map((item) => <li key={item}>{item}</li>)}</ul>}{after && <p className="mt-3">{after}</p>}</div></section>;
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-2xl border border-hairline bg-surface p-5"><h2 className="font-semibold text-accent">{title}</h2><p className="mt-2 text-sm leading-7 text-muted">{children}</p></section>;
}
