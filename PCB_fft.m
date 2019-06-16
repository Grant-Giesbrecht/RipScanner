%*********** Load data from file
%

if ~exist("CH1", "var")
	T = readtable("/Volumes/PHILIPS UFD/compressor_out_sample.csv");
	CH1 = T{:, 2};
	CH2 = T{:, 3};
	CH3 = T{:, 4};
	t0 = -3e-2;
	dt = 20e-9;
	t = T{:, 1}.*dt + t0;
end

%********* Plot waveform
%



n = 100;
figure(1);
hold off;
plot(t(1:n:end), CH1(1:n:end));
hold on;
plot(t(1:n:end), CH2(1:n:end));
plot(t(1:n:end), CH3(1:n:end));
grid on;
xL = xlim;
yL = ylim;
line([0 0], yL, 'Color', [.3, .3, .3], 'LineWidth', 1);  %y-axis
line(xL, [0 0], 'Color', [.3, .3, .3], 'LineWidth', 1);  %x-axis
xlabel('Time (s)');
ylabel('Voltage');
legend('CH 1 - Input', 'CH 2 - Output', 'CH 3 - V_Q2Base');

%************ Perform FFT
%

%Perform calculations
Fs = 1/dt;
L = length(CH1);

specCH1 = fft(CH1);
specCH2 = fft(CH2);

ch1P2 = abs(specCH1/L);
ch1P1 = ch1P2(1:L/2+1);
ch1P1(2:end-1) = 2*ch1P1(2:end-1);

ch2P2 = abs(specCH2/L);
ch2P1 = ch2P2(1:L/2+1);
ch2P1(2:end-1) = 2*ch2P1(2:end-1);

%Plot the two spectra
figure(2);
f = Fs*(0:(L/2))/L;
hold off;
semilogx(f,ch1P1) 
hold on;
semilogx(f,ch2P1, 'LineStyle', ':', 'LineWidth', 1) ;
title('Single-Sided Amplitude Spectrum of Input & Output Signals');
xlabel('f (Hz)')
ylabel('|P1(f)|')
xlim([100, 20e3]);
grid on;
legend('Input Spectrum', 'Output Spectrum');

%Plot their difference
figure(3);
hold off;
semilogx(f,ch1P1-ch2P1);
hold on;
semilogx(f,ch1P1, 'LineStyle', ':', 'LineWidth', 1, 'Color', [.8, 0, 0]);
semilogx(f,ch2P1, 'LineStyle', ':', 'LineWidth', 1, 'Color', [0, .8, 0]);
title('Difference in Input and Output Spectra');
xlabel('f (Hz)')
ylabel('|P1(f)|')
xlim([100, 20e3]);
grid on;
xL = xlim;
line(xL, [0 0], 'Color', [.3, .3, .3], 'LineWidth', 1);  %x-axis
legend('Input Spectrum - Output Spectrum','Input Spectrum', 'Output Spectrum');

%Plot their difference AFTER normalizeing the spectra
ch1P1norm = ch1P1./trapz(ch1P1);
ch2P1norm = ch2P1./trapz(ch2P1);
figure(4);
hold off;
semilogx(f,abs(ch1P1norm-ch2P1norm));
hold on;
semilogx(f,ch1P1norm, 'LineStyle', '-', 'LineWidth', 1, 'Color', [.8, 0, 0]);
semilogx(f,ch2P1norm, 'LineStyle', '-', 'LineWidth', 1, 'Color', [0, .8, 0]);
title('Difference in Input and Output Spectra');
xlabel('f (Hz)')
ylabel('|P1(f)|')
xlim([100, 20e3]);
grid on;
legend('abs(Input Spectrum - Output Spectrum)','Input Spectrum', 'Output Spectrum');