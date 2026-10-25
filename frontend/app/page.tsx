'use client';

import {useEffect, useState, type FormEvent} from 'react';
import {ArrowRight, FileText} from 'lucide-react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';

type AuthMode = 'signin' | 'signup';

export default function Home() {
	const router = useRouter();
	const [mode, setMode] = useState<AuthMode>('signin');
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [confirmPassword, setConfirmPassword] = useState('');
	const [checkingSession, setCheckingSession] = useState(true);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState('');

	useEffect(() => {
		let ignore = false;
		fetch('/api/auth/me')
			.then((response) => {
				if (ignore) return;
				if (response.ok) router.replace('/history');
				else setCheckingSession(false);
			})
			.catch(() => {
				if (!ignore) setCheckingSession(false);
			});
		return () => {
			ignore = true;
		};
	}, [router]);

	async function submit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		if (busy || checkingSession) return;
		if (mode === 'signup' && password !== confirmPassword) {
			setError('Passwords do not match.');
			return;
		}

		setBusy(true);
		setError('');
		try {
			const response = await fetch(`/api/auth/${mode}`, {
				method: 'POST',
				headers: {'Content-Type': 'application/json'},
				body: JSON.stringify({email, password}),
			});
			const result = await response.json();
			if (!response.ok) throw new Error(result.detail || 'Could not authenticate.');
			router.replace('/history');
		} catch (authError) {
			setError(authError instanceof Error ? authError.message : 'Could not authenticate.');
		} finally {
			setBusy(false);
		}
	}

	function changeMode(nextMode: AuthMode) {
		setMode(nextMode);
		setPassword('');
		setConfirmPassword('');
		setError('');
	}

	return (
		<main className='login-shell'>
			<header className='topbar login-topbar'>
				<Link className='brand' href='/' aria-label='Prelegal home'>
					<span className='brand-mark'><FileText size={17} /></span>
					<span>prelegal<span className='brand-period'>.</span></span>
				</Link>
			</header>

			<section className='login-content' aria-labelledby='login-title'>
				<div className='login-card'>
					<div className='login-icon'><FileText size={22} /></div>
					<span className='section-kicker'>YOUR AGREEMENT WORKSPACE</span>
					<h1 id='login-title'>{mode === 'signup' ? 'Create your account' : 'Welcome back'}</h1>
					<p className='login-description'>
						{mode === 'signup'
							? 'Create an account to save and revisit your NDA drafts.'
							: 'Sign in to continue to your Mutual NDA workspace.'}
					</p>

					<form className='login-form' onSubmit={submit}>
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
								value={password}
								placeholder={mode === 'signup' ? 'At least 8 characters' : 'Your password'}
								minLength={mode === 'signup' ? 8 : 1}
								maxLength={128}
								autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
								required
								onChange={(event) => setPassword(event.target.value)}
							/>
						</label>
						{mode === 'signup' && (
							<label className='field'>
								<span className='field-label'>Confirm password</span>
								<input
									type='password'
									value={confirmPassword}
									minLength={8}
									maxLength={128}
									autoComplete='new-password'
									required
									onChange={(event) => setConfirmPassword(event.target.value)}
								/>
							</label>
						)}
						<button className='login-button' type='submit' disabled={busy || checkingSession}>
							{busy ? 'Please wait…' : mode === 'signup' ? 'Create account' : 'Sign in'}
							{!busy && <ArrowRight size={16} />}
						</button>
						{error && <p className='download-error' role='alert'>{error}</p>}
					</form>

					<p className='auth-switch'>
						{mode === 'signup' ? 'Already have an account?' : 'New to Prelegal?'}{' '}
						<button type='button' onClick={() => changeMode(mode === 'signup' ? 'signin' : 'signup')}>
							{mode === 'signup' ? 'Sign in' : 'Create an account'}
						</button>
					</p>
					<p className='demo-notice'>Accounts and saved drafts are temporary and reset when the server restarts.</p>
				</div>
			</section>

			<footer className='login-footer'>
				<span>PRELEGAL · TOOLS FOR BETTER AGREEMENTS</span>
				<span>Draft only—not legal advice. Have an attorney review before signing.</span>
			</footer>
		</main>
	);
}
