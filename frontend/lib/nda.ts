export type NdaDraft = {
  partyAName: string;
  partyAAddress: string;
  partyBName: string;
  partyBAddress: string;
  effectiveDate: string;
  purpose: string;
  governingLaw: string;
};

export function getLocalDateInputValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export const initialDraft: NdaDraft = {
  partyAName: "",
  partyAAddress: "",
  partyBName: "",
  partyBAddress: "",
  effectiveDate: getLocalDateInputValue(),
  purpose: "Evaluating a potential business relationship",
  governingLaw: "California",
};

export const requiredFields: (keyof NdaDraft)[] = ["partyAName", "partyBName", "purpose"];

export function formatDate(value: string) {
  if (!value) return "[Effective date]";
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(
    new Date(`${value}T00:00:00Z`),
  );
}

export function getAgreementSections(draft: NdaDraft) {
  const partyA = draft.partyAName.trim() || "[Party A name]";
  const partyB = draft.partyBName.trim() || "[Party B name]";
  const purpose = draft.purpose.trim() || "[describe the purpose]";
  const law = draft.governingLaw.trim() || "[governing jurisdiction]";

  return [
    { heading: "1. Purpose", body: `The parties wish to explore ${purpose} (the “Purpose”). In connection with the Purpose, either party may disclose Confidential Information to the other.` },
    { heading: "2. Confidential Information", body: "“Confidential Information” means non-public information disclosed by or on behalf of a party (the “Disclosing Party”) to the other party (the “Receiving Party”), in any form, that is marked confidential or reasonably should be understood to be confidential given its nature or the circumstances of disclosure. It does not include information the Receiving Party can demonstrate is publicly available through no breach, already known without restriction, independently developed, or rightfully received from another source without a duty of confidentiality." },
    { heading: "3. Use and protection", body: "The Receiving Party will use Confidential Information only for the Purpose, protect it using reasonable care, and disclose it only to its employees and professional advisers who need to know it and are bound by confidentiality obligations at least as protective as these terms. The Receiving Party is responsible for their compliance." },
    { heading: "4. Required disclosure", body: "If the Receiving Party is legally required to disclose Confidential Information, it may do so to the extent required and, where legally permitted, will give the Disclosing Party prompt notice so that the Disclosing Party may seek a protective order." },
    { heading: "5. Term and return", body: "This Agreement begins on the Effective Date and continues for two years. The confidentiality obligations for information disclosed during the term continue for three years after disclosure. Upon request, each party will return or destroy the other party’s Confidential Information, except that one archival copy may be retained for legal or compliance purposes." },
    { heading: "6. No license or obligation", body: "All Confidential Information remains the property of the Disclosing Party. No license is granted by this Agreement. Neither party is required to proceed with a transaction, and either party may end discussions at any time." },
    { heading: "7. Disclaimer", body: "Confidential Information is provided “as is.” Neither party makes any warranty as to its accuracy or completeness. This section does not limit liability for a party’s breach of this Agreement." },
    { heading: "8. General", body: `This Agreement is governed by the laws of ${law}, excluding its conflict-of-law rules. This Agreement is the entire agreement concerning its subject matter and may be amended only in a writing signed by both parties. If any provision is unenforceable, the remaining provisions continue in effect. A party’s failure to enforce a provision is not a waiver.` },
    { heading: "Signatures", body: `The parties agree to this Mutual Non-Disclosure Agreement as of ${formatDate(draft.effectiveDate)}.\n\n${partyA}\nBy: ______________________________\nName / Title: _____________________\nDate: ____________________________\n\n${partyB}\nBy: ______________________________\nName / Title: _____________________\nDate: ____________________________` },
  ];
}

export function getAgreementText(draft: NdaDraft) {
  const partyA = draft.partyAName.trim() || "[Party A name]";
  const partyB = draft.partyBName.trim() || "[Party B name]";
  return [
    "MUTUAL NON-DISCLOSURE AGREEMENT",
    `Effective date: ${formatDate(draft.effectiveDate)}`,
    `This Mutual Non-Disclosure Agreement (the “Agreement”) is between ${partyA}${draft.partyAAddress ? `, located at ${draft.partyAAddress}` : ""}, and ${partyB}${draft.partyBAddress ? `, located at ${draft.partyBAddress}` : ""} (each a “party” and together the “parties”).`,
    ...getAgreementSections(draft).flatMap(({ heading, body }) => [heading, body]),
  ].join("\n\n");
}
