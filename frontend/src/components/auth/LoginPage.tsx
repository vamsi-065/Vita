import React, { useState } from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { api } from '../../services/api';

export function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      if (isLogin) {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) throw signInError;
      } else {
        // Validate phone number format for Indian number if provided
        let formattedPhone = phone;
        if (phone) {
          const cleanPhone = phone.replace(/\D/g, '');
          if (!/^[6-9]\d{9}$/.test(cleanPhone)) {
            throw new Error('Please enter a valid 10-digit Indian mobile number.');
          }
          formattedPhone = `+91${cleanPhone}`;
        }
        
        const { error: signUpError } = await supabase.auth.signUp({
          email,
          password,
        });
        
        if (signUpError) throw signUpError;
        
        // Setup profile phone via backend
        if (formattedPhone) {
          // Note: Backend endpoint requires auth token which will be passed via App.tsx session state
          // but if sign up requires email verification, session won't be created.
          // Wait to update profile until user logs in. If auto-login is true, session exists now.
          const { data: { session } } = await supabase.auth.getSession();
          if (session) {
            try {
              await api.updateProfile(formattedPhone);
            } catch (err) {
              console.error("Failed to link phone number:", err);
              // Do not block login if profile fails
            }
          }
        }
        
        setSuccess('Signup successful! Check your email to verify if required, or you will be logged in.');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0B0C] flex flex-col items-center justify-center p-4 font-sans text-white">
      <div className="w-full max-w-md">
        <div className="mb-12 text-center sm:text-left">
          <h1 className="text-4xl font-bold tracking-tight">Vita</h1>
        </div>

        <div className="bg-[#131314] p-8 rounded-2xl border border-[#444746] shadow-2xl transition-all duration-300">
          <h2 className="text-2xl font-semibold mb-2">
            {isLogin ? 'Welcome back' : 'Create an account'}
          </h2>
          <p className="text-[#8E8E93] mb-6">
            {isLogin 
              ? 'Sign in to continue to your workspace.' 
              : 'Sign up to manage your business.'}
          </p>

          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center">
              {error}
            </div>
          )}
          
          {success && (
            <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 text-sm text-center">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[#8E8E93]">Email Address</label>
              <input
                type="email"
                placeholder="you@company.com"
                className="w-full bg-[#0B0B0C] border border-[#444746] focus:border-[#818CF8] focus:ring-1 focus:ring-[#818CF8] text-white px-4 py-3 rounded-xl outline-none transition-all placeholder-[#8E8E93]"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                required
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-[#8E8E93]">Password</label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full bg-[#0B0B0C] border border-[#444746] focus:border-[#818CF8] focus:ring-1 focus:ring-[#818CF8] text-white px-4 py-3 rounded-xl outline-none transition-all placeholder-[#8E8E93]"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-[#8E8E93]">Phone Number (for Telegram Alerts)</label>
                <div className="flex bg-[#0B0B0C] rounded-xl border border-[#444746] focus-within:border-[#818CF8] focus-within:ring-1 focus-within:ring-[#818CF8] transition-all overflow-hidden">
                  <div className="bg-transparent text-[#8E8E93] px-3 py-3 border-r border-[#444746] text-sm flex items-center select-none">
                    +91
                  </div>
                  <input
                    type="tel"
                    placeholder="Enter 10-digit mobile number"
                    className="w-full bg-transparent text-white px-4 py-3 outline-none placeholder-[#8E8E93]"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full py-3.5 px-4 mt-2 rounded-xl font-medium text-[#131314] transition-all 
                         bg-gradient-to-r from-[#8AB4F8] via-[#C5A5FF] to-[#FF8F8F]
                         hover:opacity-90 active:scale-[0.98]
                         disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(197,165,255,0.3)]"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin text-[#131314]" />
              ) : (
                isLogin ? 'Sign In' : 'Sign Up'
              )}
            </button>
            
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                  setSuccess('');
                }}
                className="text-sm text-[#8E8E93] hover:text-white transition-colors"
              >
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
