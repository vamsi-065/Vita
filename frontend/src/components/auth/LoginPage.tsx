import React, { useState, useRef } from 'react';
import { useStore } from '../../store/useStore';
import { ArrowRight, Loader2 } from 'lucide-react';
import { supabase } from '../../lib/supabase';

export function LoginPage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Function to send code via Supabase
  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone) return;
    setIsLoading(true);
    setError('');

    const cleanPhone = phone.replace(/\D/g, '');
    if (!/^[6-9]\d{9}$/.test(cleanPhone)) {
      setError('Please enter a valid 10-digit Indian mobile number.');
      setIsLoading(false);
      return;
    }

    const fullPhone = `+91${cleanPhone}`;
    
    const { error: signInError } = await supabase.auth.signInWithOtp({
      phone: fullPhone,
    });
    
    setIsLoading(false);
    if (signInError) {
      setError(signInError.message);
    } else {
      setStep(2);
    }
  };

  // Function to verify OTP via Supabase
  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join('');
    if (code.length < 6) return;
    setIsLoading(true);
    setError('');
    
    const cleanPhone = phone.replace(/\D/g, '');
    const fullPhone = `+91${cleanPhone}`;

    const { data, error: verifyError } = await supabase.auth.verifyOtp({
      phone: fullPhone,
      token: code,
      type: 'sms',
    });

    setIsLoading(false);
    if (verifyError) {
      setError(verifyError.message);
    } else if (data?.user) {
      useStore.getState().setUser({
        id: data.user.id,
        email: data.user.email || '',
        full_name: data.user.user_metadata?.full_name || 'Vita User',
        business_name: data.user.user_metadata?.business_name || '',
        is_active: true,
        created_at: data.user.created_at || new Date().toISOString()
      });
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    // Move to next input automatically
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0B0C] flex flex-col items-center justify-center p-4 font-sans text-white">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="mb-12 text-center sm:text-left">
          <h1 className="text-4xl font-bold tracking-tight">Vita</h1>
        </div>

        {/* Card Container */}
        <div className="bg-[#131314] p-8 rounded-2xl border border-[#444746] shadow-2xl transition-all duration-300">
          <h2 className="text-2xl font-semibold mb-2">
            {step === 1 ? 'Welcome back' : 'Enter code'}
          </h2>
          <p className="text-[#8E8E93] mb-6">
            {step === 1 
              ? 'Sign in to continue to your workspace.' 
              : `We sent a code to +91 ${phone}`}
          </p>

          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleSendCode} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[#8E8E93]">Phone Number</label>
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
                    autoFocus
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading || !phone}
                className="w-full py-3.5 px-4 rounded-xl font-medium text-white transition-all 
                           bg-white/5 hover:bg-white/10 active:scale-[0.98] 
                           disabled:opacity-50 disabled:cursor-not-allowed
                           border border-white/10 hover:border-white/20
                           flex items-center justify-center gap-2 group"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Send Verification Code
                    <ArrowRight className="w-4 h-4 opacity-70 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                  </>
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex justify-between gap-2">
                {otp.map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => { otpRefs.current[i] = el; }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpChange(i, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(i, e)}
                    className="w-12 h-14 bg-[#0B0B0C] border border-[#444746] rounded-xl text-center text-xl font-semibold text-white 
                             focus:border-[#C5A5FF] focus:ring-1 focus:ring-[#C5A5FF] focus:outline-none transition-all
                             selection:bg-transparent"
                    autoFocus={i === 0}
                  />
                ))}
              </div>

              <button
                type="submit"
                disabled={isLoading || otp.join('').length < 6}
                className="w-full py-3.5 px-4 rounded-xl font-medium text-[#131314] transition-all 
                           bg-gradient-to-r from-[#8AB4F8] via-[#C5A5FF] to-[#FF8F8F]
                           hover:opacity-90 active:scale-[0.98]
                           disabled:opacity-50 disabled:cursor-not-allowed
                           flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(197,165,255,0.3)]"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin text-[#131314]" />
                ) : (
                  'Verify & Continue'
                )}
              </button>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setStep(1);
                    setOtp(['', '', '', '', '', '']);
                    setError('');
                  }}
                  className="text-sm text-[#8E8E93] hover:text-white transition-colors"
                >
                  Wrong number? Go back
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
