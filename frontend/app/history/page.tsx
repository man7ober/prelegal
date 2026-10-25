'use client';

import {useEffect, useState} from 'react';
import {ArrowRight, FileText, LogOut, Plus} from 'lucide-react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';

type SavedDocument = {
	id: string;
	title: string;
	created_at: string;
	updated_at: string;
};

function formatDate(value: string) {
	return new Intl.DateTimeFormat('en-US', {dateStyle: 'medium'}).format(new Date(value));
}

export default function HistoryPage() {
	const router = useRouter();
	const [email, setEmail] = useState('');
	const [documents, setDocuments] = useState<SavedDocument[]>([]);
	const [loading, setLoading] = useState(true);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState('');

	useEffect(() => {
		let ignore = false;
		async function loadHistory() {
			try {
				const sessionResponse = await fetch('/api/auth/me');
				if (sessionResponse.status === 401) {
					router.replace('/');
					return;
				}
				if (!sessionResponse.ok) throw new Error('Your account could not be loaded.');
				const session = await sessionResponse.json();
				const documentsResponse = await fetch('/api/documents');
				if (documentsResponse.status === 401) {
					router.replace('/');
					return;
				}
				if (!documentsResponse.ok) throw new Error('Your saved documents could not be loaded.');
				const savedDocuments = (await documentsResponse.json()) as SavedDocument[];
				if (!ignore) {
					setEmail(session.email);
					setDocuments(savedDocuments);
				}
			} catch (loadError) {
				if (!ignore) setError(loadError instanceof Error ? loadError.message : 'Could not load your documents.');
			} finally {
				if (!ignore) setLoading(false);
			}
		}
		void loadHistory();
		return () => { ignore = true; };
	}, [router]);

	async function signOut() {
		setBusy(true);
		try {
			await fetch('/api/auth/logout', {method: 'POST'});
		} finally {
			router.replace('/');
			router.refresh();
		}
	}

	return (
		<main className='app-shell account-shell'>
			<header className='topbar'>
				<Link className='brand' href='/history' aria-label='Prelegal home'>
					<span className='brand-mark'><FileText size={17} /></span>
					<span>prelegal<span className='brand-period'>.</span></span>
				</Link>
				<div className='account-actions'>
					<span>{email}</span>
					<button type='button' onClick={signOut} disabled={busy}>
						<LogOut size={14} /> Sign out
					</button>
				</div>
			</header>

			<section className='history-intro'>
				<div>
					<span className='section-kicker'>YOUR WORKSPACE</span>
					<h1>Saved NDA drafts</h1>
					<p>Return to a saved draft or start a new Mutual NDA.</p>
				</div>
				<Link className='new-document-button' href='/workspace'>
					<Plus size={16} /> New Mutual NDA
				</Link>
			</section>

			<section className='history-panel' aria-labelledby='documents-heading'>
				<div className='history-panel-heading'>
					<div>
						<span className='section-kicker'>DOCUMENT HISTORY</span>
						<h2 id='documents-heading'>Your drafts</h2>
					</div>
					<span className='history-count'>{documents.length}</span>
				</div>

				{error && <p className='download-error' role='alert'>{error}</p>}
				{loading ? (
					<p className='history-status' role='status'>Loading your documents…</p>
				) : documents.length === 0 ? (
					<div className='history-empty'>
						<FileText size={28} />
						<strong>No saved drafts yet</strong>
						<p>Your drafts will appear here when you choose Save in the NDA workspace.</p>
						<Link href='/workspace'>Start a Mutual NDA <ArrowRight size={14} /></Link>
					</div>
				) : (
					<ul className='history-list'>
						{documents.map((document) => (
							<li key={document.id}>
								<div className='history-document-icon'><FileText size={18} /></div>
								<div className='history-document-details'>
									<strong>{document.title}</strong>
									<span>Updated {formatDate(document.updated_at)}</span>
								</div>
								<Link href={`/workspace?document_id=${encodeURIComponent(document.id)}`}>
									Open draft <ArrowRight size={14} />
								</Link>
							</li>
						))}
					</ul>
				)}
			</section>

			<footer className='site-footer'>
				<span>PRELEGAL · TOOLS FOR BETTER AGREEMENTS</span>
				<span className='disclaimer'>Draft only—not legal advice. Have an attorney review before signing.</span>
			</footer>
		</main>
	);
}
