'use client';

import {useState, type FormEvent} from 'react';
import {ArrowRight, FileText} from 'lucide-react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';

export default function Home() {
	const router = useRouter();
	const [email, setEmail] = useState('');

	function continueToWorkspace(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		router.push('/workspace');
	}

	return (
		<main className='login-shell'>
			<header className='topbar login-topbar'>
				<Link className='brand' href='/' aria-label='Prelegal home'>
					<span className='brand-mark'>
						<FileText size={17} />
					</span>
					<span>
						prelegal<span className='brand-period'>.</span>
					</span>
				</Link>
			</header>

			<section className='login-content' aria-labelledby='login-title'>
				<div className='login-card'>
					<div className='login-icon'>
						<FileText size={22} />
					</div>
					<span className='section-kicker'>YOUR AGREEMENT WORKSPACE</span>
					<h1 id='login-title'>Welcome to Prelegal</h1>
					<p className='login-description'>
						Continue to your workspace to start drafting an agreement.
					</p>

					<form className='login-form' onSubmit={continueToWorkspace}>
						<label className='field'>
							<span className='field-label'>Email address</span>
							<input
								type='email'
								value={email}
								placeholder='you@example.com'
								autoComplete='email'
								required
								onChange={(event) => setEmail(event.target.value)}
							/>
						</label>
						<label className='field'>
							<span className='field-label'>Password</span>
							<input
								type='password'
								placeholder='Enter any password'
								autoComplete='current-password'
								required
							/>
						</label>
						<button className='login-button' type='submit'>
							Continue to workspace <ArrowRight size={16} />
						</button>
					</form>
					<p className='demo-notice'>
						Demo screen only — no account is created and no credentials are checked.
					</p>
				</div>
			</section>

			<footer className='login-footer'>
				<span>PRELEGAL · TOOLS FOR BETTER AGREEMENTS</span>
				<span>A starting point, not legal advice.</span>
			</footer>
		</main>
	);
}
