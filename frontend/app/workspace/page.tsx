'use client';

import {type FormEvent, useEffect, useRef, useState} from 'react';
import {Download, FileText, Send} from 'lucide-react';
import Link from 'next/link';
import {downloadDocumentPdf} from '@/lib/pdf';

type DocumentInfo = {
	id: string;
	title: string;
	description: string;
	missing_companions: string[];
};

type ChatMessage = {role: 'user' | 'assistant'; content: string};

type RenderedDocument = {
	title: string;
	html: string;
	text: string;
	missing_required: string[];
	missing_variables: string[];
	missing_companions: string[];
};

const NDA_DOCUMENT_ID = 'mutual-nda';

async function fetchRenderedDocument(
	documentId: string,
	fieldValues: Record<string, string>,
): Promise<RenderedDocument> {
	const response = await fetch(`/api/documents/${documentId}/render`, {
		method: 'POST',
		headers: {'Content-Type': 'application/json'},
		body: JSON.stringify({field_values: fieldValues}),
	});
	const result = await response.json();
	if (!response.ok)
		throw new Error(result.detail || 'The document could not be rendered.');
	return result as RenderedDocument;
}

export default function Workspace() {
	const [catalog, setCatalog] = useState<DocumentInfo[]>([]);
	const [messages, setMessages] = useState<ChatMessage[]>([
		{
			role: 'assistant',
			content:
				'I can help you prepare a Mutual Non-Disclosure Agreement. Tell me what you want to protect and who the parties are; I’ll ask for any details the template still needs.',
		},
	]);
	const [message, setMessage] = useState('');
	const documentId = NDA_DOCUMENT_ID;
	const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
	const [suggestion, setSuggestion] = useState('');
	const [consent, setConsent] = useState(false);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState('');
	const [rendered, setRendered] = useState<RenderedDocument | null>(null);
	const messageList = useRef<HTMLDivElement>(null);

	useEffect(() => {
		let ignore = false;
		async function loadWorkspace() {
			try {
				const response = await fetch('/api/documents');
				if (!response.ok)
					throw new Error('The template catalog could not be loaded.');
				const documents = (await response.json()) as DocumentInfo[];
				if (!documents.some((document) => document.id === NDA_DOCUMENT_ID)) {
					throw new Error('The Mutual NDA template is unavailable.');
				}
				const initialDraft = await fetchRenderedDocument(NDA_DOCUMENT_ID, {});
				if (!ignore) {
					setCatalog(documents);
					setRendered(initialDraft);
				}
			} catch {
				if (!ignore)
					setError(
						'The Mutual NDA template could not be loaded. Please refresh the page.',
					);
			}
		}
		void loadWorkspace();
		return () => {
			ignore = true;
		};
	}, []);

	useEffect(() => {
		messageList.current?.scrollTo({
			top: messageList.current.scrollHeight,
			behavior: 'smooth',
		});
	}, [messages]);

	const selectedDocument = catalog.find(
		(document) => document.id === NDA_DOCUMENT_ID,
	);

	async function sendMessage(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		const content = message.trim();
		if (!content || !consent || busy) return;

		const nextMessages: ChatMessage[] = [...messages, {role: 'user', content}];
		setMessages(nextMessages);
		setMessage('');
		setSuggestion('');
		setError('');
		setBusy(true);
		try {
			const response = await fetch('/api/chat', {
				method: 'POST',
				headers: {'Content-Type': 'application/json'},
				body: JSON.stringify({
					messages: nextMessages.slice(-16),
					document_id: documentId || null,
					field_values: fieldValues,
					consent: true,
				}),
			});
			const result = await response.json();
			if (!response.ok)
				throw new Error(result.detail || 'The assistant could not respond.');
			const updatedValues = (result.field_values || {}) as Record<
				string,
				string
			>;
			setFieldValues(updatedValues);
			setSuggestion(result.suggested_document_id || '');
			setMessages((current) => [
				...current,
				{role: 'assistant', content: result.message},
			]);
			try {
				setRendered(
					await fetchRenderedDocument(NDA_DOCUMENT_ID, updatedValues),
				);
			} catch {
				setError(
					'The reply was received, but the document preview could not be refreshed.',
				);
			}
		} catch (requestError) {
			setError(
				requestError instanceof Error
					? requestError.message
					: 'The assistant could not respond.',
			);
		}
		setBusy(false);
	}

	return (
		<main className='app-shell guided-shell'>
			<header className='topbar'>
				<Link
					className='brand'
					href='/'
					aria-label='Prelegal home'>
					<span className='brand-mark'>
						<FileText size={17} />
					</span>
					<span>
						prelegal<span className='brand-period'>.</span>
					</span>
				</Link>
				<span className='guided-label'>AGREEMENT STUDIO</span>
			</header>

			<section className='guided-intro'>
				<span className='section-kicker'>GUIDED DOCUMENT DRAFTING</span>
				<h1>Let’s find the right agreement.</h1>
				<p>
					Share what you need. The assistant will help collect details and
					prepare a draft from the selected template.
				</p>
			</section>

			<div className='guided-layout'>
				<section
					className='chat-panel'
					aria-label='Agreement drafting conversation'>
					<div className='chat-heading'>
						<div>
							<span className='section-kicker'>YOUR ASSISTANT</span>
							<h2>Your Mutual NDA</h2>
						</div>
						{selectedDocument && (
							<span className='selected-type'>{selectedDocument.title}</span>
						)}
					</div>

					<div
						className='chat-messages'
						ref={messageList}
						aria-live='polite'>
						{messages.map((item, index) => (
							<div
								className={`chat-message ${item.role}`}
								key={`${item.role}-${index}`}>
								<span>{item.role === 'assistant' ? 'PRELEGAL' : 'YOU'}</span>
								<p>{item.content}</p>
							</div>
						))}
						{busy && (
							<p
								className='chat-loading'
								role='status'>
								Preparing your response…
							</p>
						)}
					</div>

					{suggestion && (
						<div className='suggestion-card'>
							<p>
								This request is outside the current Mutual NDA template. The
								closest available option is:
							</p>
							<button
								type='button'
								onClick={() => {
									const suggested = catalog.find(
										(item) => item.id === suggestion,
									);
									if (suggested) {
										setMessage(
											`I would like to continue with a ${suggested.title}.`,
										);
									}
								}}>
								{catalog.find((item) => item.id === suggestion)?.title ||
									'Suggested agreement'}
							</button>
						</div>
					)}

					<form
						className='chat-form'
						onSubmit={sendMessage}>
						<label
							className='sr-only'
							htmlFor='message'>
							Describe the agreement you need
						</label>
						<textarea
							id='message'
							value={message}
							placeholder='For example: I need to protect information while discussing a possible partnership…'
							maxLength={2000}
							onChange={(event) => setMessage(event.target.value)}
						/>
						<div className='chat-form-bottom'>
							<label className='consent-label'>
								<input
									type='checkbox'
									checked={consent}
									onChange={(event) => setConsent(event.target.checked)}
								/>
								<span>
									I understand messages and provided details are sent to
									OpenRouter for AI assistance. They aren’t saved to an account
									or database.
								</span>
							</label>
							<button
								className='send-button'
								type='submit'
								disabled={!consent || !message.trim() || busy}>
								Send <Send size={15} />
							</button>
						</div>
						<p className='privacy-note'>
							Don’t enter health information or other highly sensitive personal
							data. This is a general template, not legal advice.
						</p>
					</form>
					{error && (
						<p
							className='download-error'
							role='alert'>
							{error}
						</p>
					)}
				</section>

				<aside
					className='draft-panel'
					aria-label='Draft document'>
					<div className='draft-heading'>
						<div>
							<span className='section-kicker'>DOCUMENT PREVIEW</span>
							<h2>
								{rendered?.title || selectedDocument?.title || 'Your agreement'}
							</h2>
						</div>
						<span className='live-pill'>
							<span /> LIVE PREVIEW
						</span>
					</div>

					{rendered ? (
						<>
							{(rendered.missing_required.length > 0 ||
								rendered.missing_variables.length > 0 ||
								rendered.missing_companions.length > 0) && (
								<div
									className='draft-warning'
									role='status'>
									<strong>Review before using this draft.</strong>
									{rendered.missing_required.length > 0 && (
										<p>
											Details still needed:{' '}
											{rendered.missing_required.join(', ')}.
										</p>
									)}
									{rendered.missing_variables.length > 0 && (
										<p>
											Unfilled template variables:{' '}
											{rendered.missing_variables.slice(0, 6).join(', ')}
											{rendered.missing_variables.length > 6
												? `, and ${rendered.missing_variables.length - 6} more`
												: ''}
											.
										</p>
									)}
									{rendered.missing_companions.length > 0 && (
										<p>
											The source terms refer to companion documents not included
											in this catalog: {rendered.missing_companions.join(', ')}.
											They are not generated here.
										</p>
									)}
								</div>
							)}
							<div
								className='rendered-document'
								dangerouslySetInnerHTML={{__html: rendered.html}}
							/>
							<button
								className='download-button'
								type='button'
								onClick={() =>
									downloadDocumentPdf(rendered.title, rendered.text)
								}>
								Download PDF <Download size={16} />
							</button>
						</>
					) : (
						<div className='empty-draft'>
							<FileText size={28} />
							<p>
								Describe your NDA and the assistant will update this
								template-based draft as it gathers details.
							</p>
						</div>
					)}
				</aside>
			</div>

			<footer className='site-footer'>
				<span>PRELEGAL · TOOLS FOR BETTER AGREEMENTS</span>
				<span className='disclaimer'>
					A starting point, not legal advice. Have an attorney review generated
					drafts.
				</span>
			</footer>
		</main>
	);
}
