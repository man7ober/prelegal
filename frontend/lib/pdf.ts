import type { NdaDraft } from "./nda";
import { getAgreementText } from "./nda";

export async function downloadDocumentPdf(title: string, text: string) {
  const { jsPDF } = await import("jspdf");
  const pdf = new jsPDF({ unit: "pt", format: "letter" });
  const margin = 52;
  const width = pdf.internal.pageSize.getWidth() - margin * 2;
  const pageBottom = pdf.internal.pageSize.getHeight() - margin;
  const disclaimer = "Draft only—not legal advice. Have an attorney review before signing.";
  const paragraphs = text
    .replace(/\r/g, "")
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  paragraphs.push(disclaimer);
  let y = margin;

  pdf.setFont("times", "bold");
  pdf.setFontSize(16);
  const titleLines = pdf.splitTextToSize(title, width) as string[];
  pdf.text(titleLines, margin, y);
  y += titleLines.length * 20 + 14;

  pdf.setFont("times", "normal");
  pdf.setFontSize(10);
  for (const paragraph of paragraphs) {
    const isDisclaimer = paragraph === disclaimer;
    if (isDisclaimer) {
      pdf.setFont("times", "italic");
      pdf.setFontSize(9);
    }
    const lines = pdf.splitTextToSize(paragraph, width) as string[];
    const height = lines.length * (isDisclaimer ? 12 : 14) + (isDisclaimer ? 12 : 8);
    if (y + height > pageBottom) {
      pdf.addPage();
      y = margin;
    }
    pdf.text(lines, margin, y);
    y += height;
    if (isDisclaimer) {
      pdf.setFont("times", "normal");
      pdf.setFontSize(10);
    }
  }

  const filename = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "agreement";
  pdf.save(`${filename}.pdf`);
}

export async function downloadAgreementPdf(draft: NdaDraft) {
  const { jsPDF } = await import("jspdf");
  const pdf = new jsPDF({ unit: "pt", format: "letter" });
  const margin = 58;
  const width = pdf.internal.pageSize.getWidth() - margin * 2;
  let y = margin;
  const blocks = getAgreementText(draft).split("\n\n");

  blocks.forEach((block, index) => {
    const isTitle = index === 0;
    const isHeading = /^\d+\.|^Signatures$/.test(block);
    pdf.setFont("times", isTitle || isHeading ? "bold" : "normal");
    pdf.setFontSize(isTitle ? 17 : isHeading ? 12 : 10.5);
    const lines = pdf.splitTextToSize(block, width) as string[];
    const lineHeight = isTitle ? 23 : isHeading ? 17 : 15;
    const height = lines.length * lineHeight + (isTitle || isHeading ? 5 : 12);

    if (y + height > pdf.internal.pageSize.getHeight() - margin) {
      pdf.addPage();
      y = margin;
    }

    pdf.text(lines, margin, y, { maxWidth: width });
    y += height;
  });

  const filename = (draft.partyBName.trim() || "mutual-nda")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "mutual-nda";
  pdf.save(`${filename}-mutual-nda.pdf`);
}
