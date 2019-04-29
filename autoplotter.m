clear all;

% load_kv1("TE108_lpf_flat.kv1");
load_kv1("test.kv1");

semilogx(freqs, 20*log10(out_vpp./in_vpp), 'Marker', '*', 'LineStyle', ':', 'Color', [0, 0, .9]);
title('Bode Plot');
xlabel('Frequency (Hz)');
ylabel('Gain (dB)');
xlim([10, 25e3]);
ylim([-40, 40]);
grid on;