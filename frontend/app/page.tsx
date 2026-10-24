'use client';

import {useState} from 'react';
import {
	ArrowRight,
	Check,
	Download,
	FileText,
	LockKeyhole,
	Sparkles,
} from 'lucide-react';
import {downloadAgreementPdf} from '@/lib/pdf';
import {
	formatDate,
	getAgreementSections,
	initialDraft,
	requiredFields,
	type NdaDraft,
} from '@/lib/nda';

function Field({
	label,
	value,
	onChange,
	placeholder,
	type = 'text',
	hint,
}: {
	label: string;
	value: string;
	onChange: (value: string) => void;
	placeholder?: string;
	type?: string;
	hint?: string;
}) {
	return (
		<label className='field'>
			<span className='field-label'>{label}</span>
			<input
				type={type}
				value={value}
				placeholder={placeholder}
				onChange={(event) => onChange(event.target.value)}
			/>
			{hint && <span className='field-hint'>{hint}</span>}
		</label>
	);
}

export default function Home() {
	const [draft, setDraft] = useState<NdaDraft>(initialDraft);
	const [downloading, setDownloading] = useState(false);
	const [downloadError, setDownloadError] = useState('');
	const missing = requiredFields.filter((field) => !draft[field].trim());
	const update = (field: keyof NdaDraft, value: string) =>
		setDraft((current) => ({...current, [field]: value}));

	async function download() {
		if (missing.length) {
			setDownloadError(
				'Add both party names and a purpose before downloading.',
			);
			return;
		}
		setDownloading(true);
		setDownloadError('');
		try {
			await downloadAgreementPdf(draft);
		} catch {
			setDownloadError('The PDF could not be created. Please try again.');
		} finally {
			setDownloading(false);
		}
	}

	return (
		<main className='app-shell'>
			<header className='topbar'>
				<a
					className='brand'
					href='#top'
					aria-label='Prelegal home'>
					<span className='brand-mark'>
						<FileText size={17} />
					</span>
					<span>
						prelegal<span className='brand-period'>.</span>
					</span>
				</a>
				<div className='topbar-right'>
					<span className='secure-label'>
						<LockKeyhole size={13} /> Your details stay on this device
					</span>
					<span className='topbar-divider' />
					<span className='product-label'>
						AGREEMENT STUDIO <span>01 / 03</span>
					</span>
				</div>
			</header>

			<section
				className='intro'
				id='top'>
				<div className='eyebrow'>
					<span className='eyebrow-line' /> A BETTER WAY TO GET STARTED
				</div>
			</section>

			<div className='workspace'>
				<section
					className='form-panel'
					aria-labelledby='details-title'>
					<div className='panel-heading'>
						<div>
							<span className='section-kicker'>01 — THE DETAILS</span>
							<h2 id='details-title'>Set the scene</h2>
							<p>A few details make this agreement yours.</p>
						</div>
						<span className='required-note'>
							<span>*</span> Required
						</span>
					</div>

					<div className='form-section'>
						<div className='form-section-title'>
							<span className='section-number'>A</span>
							<div>
								<h3>First party</h3>
								<p>The person or organization sharing information.</p>
							</div>
						</div>
						<Field
							label='First party legal name *'
							value={draft.partyAName}
							placeholder='e.g. Acme, Inc.'
							onChange={(value) => update('partyAName', value)}
						/>
						<Field
							label='First party business address'
							value={draft.partyAAddress}
							placeholder='Street, city, state, ZIP'
							onChange={(value) => update('partyAAddress', value)}
						/>
					</div>

					<div className='form-section'>
						<div className='form-section-title'>
							<span className='section-number'>B</span>
							<div>
								<h3>Second party</h3>
								<p>The other side of the conversation.</p>
							</div>
						</div>
						<Field
							label='Second party legal name *'
							value={draft.partyBName}
							placeholder='e.g. Jordan Lee or Acme, Inc.'
							onChange={(value) => update('partyBName', value)}
						/>
						<Field
							label='Second party business address'
							value={draft.partyBAddress}
							placeholder='Street, city, state, ZIP'
							onChange={(value) => update('partyBAddress', value)}
						/>
					</div>

					<div className='form-section final-form-section'>
						<div className='form-section-title'>
							<span className='section-number'>C</span>
							<div>
								<h3>Working together</h3>
								<p>Define the conversation you want to protect.</p>
							</div>
						</div>
						<Field
							label='Effective date'
							value={draft.effectiveDate}
							type='date'
							onChange={(value) => update('effectiveDate', value)}
						/>
						<Field
							label='Purpose *'
							value={draft.purpose}
							placeholder='What are you exploring together?'
							hint='A short phrase is perfect.'
							onChange={(value) => update('purpose', value)}
						/>
						<Field
							label='Governing law'
							value={draft.governingLaw}
							placeholder='e.g. California'
							hint='The state or country whose laws apply.'
							onChange={(value) => update('governingLaw', value)}
						/>
					</div>

					<div className='form-footer'>
						<span>
							<LockKeyhole size={14} /> Private by design. Nothing is uploaded.
						</span>
					</div>
				</section>

				<section
					className='preview-panel'
					aria-labelledby='preview-title'>
					<div className='preview-toolbar'>
						<div>
							<span className='section-kicker'>02 — LIVE PREVIEW</span>
							<h2 id='preview-title'>Your agreement</h2>
						</div>
						<span className='live-pill'>
							<span /> LIVE
						</span>
					</div>

					<div className='download-area'>
						<div className='download-caption'>
							<span className='download-icon'>
								<FileText size={17} />
							</span>
							<span>
								<strong>Ready when you are</strong>
								<small>Your document, formatted and yours to keep.</small>
							</span>
						</div>
						<button
							className='download-button'
							onClick={download}
							disabled={downloading}>
							{downloading ? 'Preparing…' : 'Download PDF'}
							<Download size={16} />
						</button>
					</div>

					<div
						className='paper-wrap'
						tabIndex={0}
						role='region'
						aria-label='Scrollable agreement preview'>
						<article
							className='paper'
							aria-label='Mutual NDA document preview'>
							<div className='paper-topline'>
								<span>
									PRELEGAL <i> / </i> AGREEMENT
								</span>
								<span>
									DRAFT · {formatDate(draft.effectiveDate).toUpperCase()}
								</span>
							</div>
							<h3 className='document-title'>
								Mutual Non-Disclosure
								<br />
								Agreement
							</h3>
							<p className='document-lede'>
								A simple agreement to keep shared ideas and information between
								the parties.
							</p>
							<p className='document-opening'>
								This Mutual Non-Disclosure Agreement (“Agreement”) is between{' '}
								<strong>{draft.partyAName || '[Party A name]'}</strong>
								{draft.partyAAddress
									? `, located at ${draft.partyAAddress}`
									: ''}
								, and <strong>{draft.partyBName || '[Party B name]'}</strong>
								{draft.partyBAddress
									? `, located at ${draft.partyBAddress}`
									: ''}{' '}
								(each a “party” and together the “parties”), effective{' '}
								{formatDate(draft.effectiveDate)}.
							</p>
							<div className='document-body'>
								{getAgreementSections(draft).map((section) => (
									<section
										key={section.heading}
										className='document-section'>
										<h4>{section.heading}</h4>
										<p>{section.body}</p>
									</section>
								))}
							</div>
							<div className='paper-footer'>
								<span>PREPARED WITH PRELEGAL</span>
								<span>
									{' '}
									MUTUAL NDA <i>·</i> {draft.governingLaw || 'JURISDICTION'}
								</span>
							</div>
						</article>
					</div>
					{downloadError && (
						<p
							role='alert'
							className='download-error'>
							{downloadError}
						</p>
					)}
					<p className='download-footnote'>
						<Check size={13} /> Print-ready PDF <span>·</span> No watermark{' '}
						<span>·</span> Generated on your device
					</p>
				</section>
			</div>

			<footer className='site-footer'>
				<span>
					PRELEGAL <i>·</i> TOOLS FOR BETTER AGREEMENTS
				</span>
				<span className='disclaimer'>
					<strong>A starting point, not legal advice.</strong> This prototype
					provides a general template only. Have an attorney review it for your
					situation.
				</span>
				<span>© 2026 PRELEGAL</span>
			</footer>
		</main>
	);
}
