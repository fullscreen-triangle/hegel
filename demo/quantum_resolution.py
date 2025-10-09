import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pandas as pd
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Set publication-quality style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'text.usetex': False,  # Set to True if you have LaTeX installed
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Data from your results
data = {
    "n_trials": 100,
    "success_rate": 0.57,
    "mean_accuracy": 0.9906800669870858,
    "std_accuracy": 0.00647358754219899,
    "raw_accuracies": [0.9959737132240899, 0.9908938855906305, 0.9971815083048056, 0.999, 0.9901267730022133, 0.9901269043444065, 0.999, 0.9981394778332232, 0.9882442049125204, 0.9963404803486877, 0.9882926584575003, 0.9882741619714379, 0.9939356981725282, 0.9766937580427376, 0.9782006573398957, 0.9875016997660722, 0.9838973510373246, 0.9945139786607622, 0.9847358073958303, 0.9807015703893177, 0.999, 0.9901937895961077, 0.9925402256375034, 0.9806020145102924, 0.9876449382037985, 0.9928873807176789, 0.9827920513806215, 0.9950055841467653, 0.9871948904806496, 0.9896664500016538, 0.9871863471021648, 0.999, 0.9918920222020965, 0.9835383125683528, 0.9985803592968255, 0.9822332508002318, 0.993670908760038, 0.9763226390089618, 0.9813745116088125, 0.993574889886953, 0.9979077326399632, 0.9933709462495197, 0.9910748137408941, 0.9895911704352857, 0.9801718240770606, 0.9862412463328423, 0.9883148898323217, 0.999, 0.9947489463165476, 0.9778956787570982, 0.9945926717551583, 0.9889193417566695, 0.9865846239975523, 0.996893410310727, 0.999, 0.999, 0.9852862598142189, 0.9895263009931903, 0.9946501074512285, 0.999, 0.9881666060972377, 0.9905147281866895, 0.9831493202079518, 0.9824303470073547, 0.9985002065791536, 0.999, 0.9914239190273573, 0.999, 0.994893088200381, 0.986839041963159, 0.9948911648440673, 0.999, 0.9917133916871204, 0.999, 0.971042039167282, 0.9985752200350018, 0.9926963765459054, 0.989607941196273, 0.992734086212284, 0.9760994486831929, 0.9902426248972999, 0.994856900572094, 0.999, 0.9878538382538108, 0.9855320511768545, 0.9879859436513238, 0.999, 0.9946300088772775, 0.9877619183698637, 0.9961061394649069, 0.9927766203947843, 0.999, 0.9863835752489811, 0.9893787028272178, 0.9888631347749427, 0.9802918804149431, 0.9943689622165166, 0.9940884421774391, 0.9920409076531397, 0.9901233029329988],
    "raw_confidences": [0.7876094605237058, 0.7630599858854445, 0.8423590916837026, 0.6810712529801022, 0.5177315622279298, 0.773964880715854, 0.7990657572825669, 0.9658495247802628, 0.8347068256974456, 0.7013066831028609, 0.5409868250889723, 0.8159871301249082, 0.9504373110415684, 0.6772411343277916, 0.7439976171739076, 0.815661298040665, 0.7493422692359916, 0.9039352707783028, 0.8566419667983376, 0.644878764308078, 0.8251194934820395, 0.8894757591556605, 0.776402310868363, 0.6398540565931614, 0.9237461640852896, 0.681305620637673, 0.7184230482413938, 0.8518554825125505, 0.9365502664116839, 0.9408477513746883, 0.7449351744573598, 0.9306141405521797, 0.7634600615755895, 0.791307148646094, 0.7399944564896437, 0.9183591287432658, 0.5084236303068026, 0.7598769057341919, 0.9247129887083673, 0.8490129326217108, 0.9707163439066254, 0.9071638521334359, 0.7533666034765611, 0.9016742417606088, 0.921428615290291, 0.6294152389045081, 0.7366250558175691, 0.7177764606283579, 0.9379136422031489, 0.9691384195747585, 0.9675690660438957, 0.6922530225782224, 0.8659407203492075, 0.9610408987132603, 0.7400994019141716, 0.8958283012661838, 0.6704631145349559, 0.8327821105538566, 0.8428165508123118, 0.8067401567701546, 0.8674116145780711, 0.7752654625939803, 0.8752000022034242, 0.8511242136991019, 0.4797922714477751, 0.7957034995907721, 0.909885542299016, 0.8781657552848494, 0.8950601756023749, 0.8843324156095349, 0.7642921726770714, 0.9093931521217, 0.8060800761205874, 0.875158077082969, 0.8521705846944331, 0.9138229442418673, 0.7668223107571569, 0.831483578861713, 0.7635077362261076, 0.9468456581582976, 0.9493213237766873, 0.7460874300565289, 0.6134718346008601, 0.6950742745563656, 0.46135932143052716, 0.909846244881368, 0.4834536069453067, 0.6575531600217343, 0.8163449074943117, 0.7133202419572728, 0.7676412776059969, 0.5145489775450864, 0.8755980267159307, 0.7445070044944053, 0.6990364619819274, 0.9759161137683459, 0.7144787732314659, 0.9672298299969009, 0.7070122319269116, 0.6764013078226409],
    "test_molecules": ["glucose", "atp", "dopamine", "caffeine", "insulin"] * 20,
    "processing_times_microseconds": [7.889530497623503e-09, 1.3797521971241586e-08, 1.370184240670071e-08, 1.6475990155667296e-08, 1.4946006606751656e-08, 1.0240840510758065e-07, 2.0074635703448163e-08, 4.2413931579480524e-08, 2.2709741251283575e-07, 6.423811416465937e-08, 1.1012890836523804e-07, 1.8912851711321647e-08, 2.1355098099509507e-08, 4.17272127175653e-09, 1.8504734406558087e-08, 3.265481186311455e-08, 1.9481181748310793e-08, 9.288590786036756e-09, 1.2855621349335252e-08, 6.176293433653791e-08, 2.3109220634509657e-08, 4.529811155109185e-08, 7.000051847143304e-08, 1.1724574340125422e-07, 4.010573010001542e-09, 1.6064942438261196e-07, 9.885936903672964e-08, 8.529543037633425e-09, 2.0681346984880906e-07, 2.536693546378928e-07, 6.30228275601634e-09, 3.241768431286508e-08, 1.6409351832266424e-07, 1.3793572402143084e-07, 2.0397963206180048e-08, 2.3489903118153323e-08, 4.6278511002436973e-08, 6.626625646686143e-08, 9.63001834058552e-08, 4.6031256300035116e-08, 6.208911092209176e-08, 1.3762289403898424e-07, 3.737295232147846e-09, 2.909366218823972e-08, 1.2494918749560258e-07, 2.2557667543306134e-07, 7.167791122084008e-08, 7.595295023530689e-08, 1.1336133854066337e-08, 5.9314324608355085e-08, 7.606067990552899e-08, 2.7769280326065332e-08, 3.136746118785438e-08, 4.7366498480247195e-08, 2.0275360750314513e-09, 3.8872476125613575e-08, 2.3755693562362987e-08, 3.967492302319826e-08, 1.2756310328478126e-08, 2.2120798999430245e-07, 9.003988138795598e-08, 1.1366329578930315e-07, 1.5567090323777913e-07, 6.900364218488851e-08, 9.093209451745585e-09, 7.702583632948226e-08, 8.839230578713735e-08, 1.3682166488084092e-07, 5.650346493829821e-08, 1.3648466672931222e-08, 3.337621802617039e-08, 4.511148254746234e-08, 1.0382246116218616e-07, 8.457817212014196e-08, 4.4020675965180616e-08, 4.3061957721698123e-07, 9.308330084672092e-08, 2.707945287567999e-08, 1.0734300462488685e-08, 1.6588829258982586e-08, 2.8230684939514094e-08, 1.75164874954294e-08, 2.064917454545804e-08, 3.356058482154465e-08, 1.90402433662887e-08, 2.2707514493559152e-07, 8.363571259200015e-09, 7.434123501127026e-08, 5.283055564893023e-08, 4.0386421660159203e-07, 1.188273456974049e-08, 5.072579937424304e-08, 3.489059664126715e-07, 2.0062440619681546e-07, 1.6986630340361793e-07, 2.9827508353350464e-08, 1.8739953278648756e-08, 1.1045595986817835e-07, 2.6503850949599554e-07, 8.136504219047423e-08],
    "quantum_efficiency": 0.973,
    "enaqt_enhancement_factor": 2.35,
    "coherence_time_microseconds": 125.0,
    "resolution_target_met": False
}

# Create DataFrame for analysis
df = pd.DataFrame({
    'accuracy': data['raw_accuracies'],
    'confidence': data['raw_confidences'],
    'molecule': data['test_molecules'],
    'processing_time': data['processing_times_microseconds']
})

# Figure 1: Accuracy Distribution and Statistical Summary
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Subplot 1: Accuracy histogram with normal distribution overlay
ax1.hist(data['raw_accuracies'], bins=20, density=True, alpha=0.7,
         color='skyblue', edgecolor='black', linewidth=0.5)
x = np.linspace(min(data['raw_accuracies']), max(data['raw_accuracies']), 100)
ax1.plot(x, stats.norm.pdf(x, data['mean_accuracy'], data['std_accuracy']),
         'r-', linewidth=2, label=f'Normal fit (μ={data["mean_accuracy"]:.4f}, σ={data["std_accuracy"]:.4f})')
ax1.axvline(data['mean_accuracy'], color='red', linestyle='--', linewidth=2, label='Mean')
ax1.set_xlabel('Accuracy')
ax1.set_ylabel('Density')
ax1.set_title('A) Accuracy Distribution with Normal Fit')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Subplot 2: Box plot by molecule type
df.boxplot(column='accuracy', by='molecule', ax=ax2)
ax2.set_title('B) Accuracy Distribution by Molecule Type')
ax2.set_xlabel('Molecule')
ax2.set_ylabel('Accuracy')
ax2.tick_params(axis='x', rotation=45)

# Subplot 3: Confidence vs Accuracy scatter plot
colors = ['red', 'blue', 'green', 'orange', 'purple']
molecules = df['molecule'].unique()
for i, mol in enumerate(molecules):
    mask = df['molecule'] == mol
    ax3.scatter(df[mask]['confidence'], df[mask]['accuracy'],
               alpha=0.6, c=colors[i], label=mol, s=30)

# Add correlation line
z = np.polyfit(df['confidence'], df['accuracy'], 1)
p = np.poly1d(z)
ax3.plot(df['confidence'], p(df['confidence']), "r--", alpha=0.8, linewidth=2)
correlation = np.corrcoef(df['confidence'], df['accuracy'])[0,1]
ax3.set_xlabel('Confidence Score')
ax3.set_ylabel('Accuracy')
ax3.set_title(f'C) Accuracy vs Confidence (r={correlation:.3f})')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Subplot 4: Processing time distribution (log scale)
processing_times_ns = np.array(data['processing_times_microseconds']) * 1e9  # Convert to nanoseconds
ax4.hist(processing_times_ns, bins=25, alpha=0.7, color='lightgreen',
         edgecolor='black', linewidth=0.5)
ax4.set_xlabel('Processing Time (nanoseconds)')
ax4.set_ylabel('Frequency')
ax4.set_title('D) Processing Time Distribution')
ax4.set_yscale('log')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bayesian_network_analysis_fig1.png', dpi=300, bbox_inches='tight')
plt.show()

# Figure 2: Performance Metrics and Quantum Enhancement
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Subplot 1: Success rate and key metrics
metrics = ['Success Rate', 'Mean Accuracy', 'Quantum Efficiency', 'ENAQT Enhancement']
values = [data['success_rate'], data['mean_accuracy'],
          data['quantum_efficiency'], data['enaqt_enhancement_factor']/10]  # Scale enhancement for visualization
colors_metrics = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

bars = ax1.bar(metrics, values, color=colors_metrics, alpha=0.8, edgecolor='black', linewidth=1)
ax1.set_ylabel('Score')
ax1.set_title('A) Key Performance Metrics')
ax1.set_ylim(0, 1.1)

# Add value labels on bars
for bar, value in zip(bars, [data['success_rate'], data['mean_accuracy'],
                             data['quantum_efficiency'], data['enaqt_enhancement_factor']]):
    height = bar.get_height()
    if value == data['enaqt_enhancement_factor']:
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.2f}×', ha='center', va='bottom', fontweight='bold')
    else:
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')

ax1.tick_params(axis='x', rotation=45)
ax1.grid(True, alpha=0.3, axis='y')

# Subplot 2: Molecule-specific performance
molecule_stats = df.groupby('molecule').agg({
    'accuracy': ['mean', 'std'],
    'confidence': 'mean'
}).round(4)

molecule_names = molecule_stats.index
accuracy_means = molecule_stats[('accuracy', 'mean')]
accuracy_stds = molecule_stats[('accuracy', 'std')]
confidence_means = molecule_stats[('confidence', 'mean')]

x_pos = np.arange(len(molecule_names))
bars1 = ax2.bar(x_pos - 0.2, accuracy_means, 0.4, yerr=accuracy_stds,
                label='Accuracy', alpha=0.8, capsize=5, color='lightblue', edgecolor='black')
bars2 = ax2.bar(x_pos + 0.2, confidence_means, 0.4,
                label='Confidence', alpha=0.8, color='lightcoral', edgecolor='black')

ax2.set_xlabel('Molecule Type')
ax2.set_ylabel('Score')
ax2.set_title('B) Performance by Molecule Type')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(molecule_names, rotation=45)
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

# Subplot 3: Temporal performance (trials over time)
trial_numbers = np.arange(1, len(data['raw_accuracies']) + 1)
# Calculate moving average
window_size = 10
moving_avg = pd.Series(data['raw_accuracies']).rolling(window=window_size).mean()

ax3.plot(trial_numbers, data['raw_accuracies'], 'o-', alpha=0.5, markersize=3,
         color='lightblue', label='Individual Trials')
ax3.plot(trial_numbers[window_size-1:], moving_avg[window_size-1:],
         'r-', linewidth=2, label=f'{window_size}-Trial Moving Average')
ax3.axhline(y=data['mean_accuracy'], color='green', linestyle='--',
            linewidth=2, label='Overall Mean')
ax3.fill_between(trial_numbers,
                 data['mean_accuracy'] - data['std_accuracy'],
                 data['mean_accuracy'] + data['std_accuracy'],
                 alpha=0.2, color='green', label='±1σ')

ax3.set_xlabel('Trial Number')
ax3.set_ylabel('Accuracy')
ax3.set_title('C) Accuracy Over Time')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Subplot 4: Quantum coherence and enhancement visualization
coherence_data = [data['coherence_time_microseconds'], 100, 75, 50]  # Example comparison values
enhancement_data = [data['enaqt_enhancement_factor'], 1.0, 1.5, 2.0]  # Comparison with classical methods
labels = ['ENAQT\n(This Work)', 'Classical\nBayesian', 'Hybrid\nQuantum', 'Standard\nML']

x_pos = np.arange(len(labels))
ax4_twin = ax4.twinx()

bars1 = ax4.bar(x_pos - 0.2, coherence_data, 0.4, alpha=0.8,
                color='gold', label='Coherence Time (μs)', edgecolor='black')
bars2 = ax4_twin.bar(x_pos + 0.2, enhancement_data, 0.4, alpha=0.8,
                     color='mediumorchid', label='Enhancement Factor', edgecolor='black')

ax4.set_xlabel('Method')
ax4.set_ylabel('Coherence Time (μs)', color='gold')
ax4_twin.set_ylabel('Enhancement Factor', color='mediumorchid')
ax4.set_title('D) Quantum Enhancement Comparison')
ax4.set_xticks(x_pos)
ax4.set_xticklabels(labels, rotation=45)

# Add legends
ax4.legend(loc='upper left')
ax4_twin.legend(loc='upper right')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bayesian_network_analysis_fig2.png', dpi=300, bbox_inches='tight')
plt.show()

# Figure 3: Statistical Analysis and Error Metrics
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Subplot 1: Q-Q plot for normality assessment
stats.probplot(data['raw_accuracies'], dist="norm", plot=ax1)
ax1.set_title('A) Q-Q Plot: Accuracy Distribution Normality')
ax1.grid(True, alpha=0.3)

# Subplot 2: Confidence intervals
confidence_levels = [0.90, 0.95, 0.99]
ci_values = []
for cl in confidence_levels:
    alpha = 1 - cl
    ci = stats.t.interval(cl, len(data['raw_accuracies'])-1,
                         loc=data['mean_accuracy'],
                         scale=data['std_accuracy']/np.sqrt(len(data['raw_accuracies'])))
    ci_values.append((ci[1] - ci[0])/2)  # Half-width

ax2.bar([f'{int(cl*100)}%' for cl in confidence_levels], ci_values,
        alpha=0.8, color='lightsteelblue', edgecolor='black')
ax2.set_ylabel('Confidence Interval Half-Width')
ax2.set_title('B) Confidence Intervals for Mean Accuracy')
ax2.grid(True, alpha=0.3, axis='y')

# Add value labels
for i, (cl, ci_val) in enumerate(zip(confidence_levels, ci_values)):
    ax2.text(i, ci_val + 0.0001, f'{ci_val:.4f}', ha='center', va='bottom', fontweight='bold')

# Subplot 3: Residuals analysis
predicted_accuracy = np.full_like(data['raw_accuracies'], data['mean_accuracy'])
residuals = np.array(data['raw_accuracies']) - predicted_accuracy

ax3.scatter(predicted_accuracy, residuals, alpha=0.6, s=30)
ax3.axhline(y=0, color='red', linestyle='--', linewidth=2)
ax3.set_xlabel('Predicted Accuracy')
ax3.set_ylabel('Residuals')
ax3.set_title('C) Residuals vs Predicted Values')
ax3.grid(True, alpha=0.3)

# Subplot 4: Performance summary table as heatmap
summary_data = {
    'Metric': ['Mean Accuracy', 'Std Accuracy', 'Success Rate', 'Quantum Efficiency',
               'Enhancement Factor', 'Coherence Time (μs)'],
    'Value': [data['mean_accuracy'], data['std_accuracy'], data['success_rate'],
              data['quantum_efficiency'], data['enaqt_enhancement_factor'],
              data['coherence_time_microseconds']],
    'Target': [0.95, 0.01, 0.80, 0.90, 2.0, 100.0],  # Example target values
    'Status': ['Excellent', 'Good', 'Needs Improvement', 'Excellent', 'Good', 'Excellent']
}

# Create a simple table visualization
table_data = []
for i, (metric, value, target, status) in enumerate(zip(summary_data['Metric'],
                                                       summary_data['Value'],
                                                       summary_data['Target'],
                                                       summary_data['Status'])):
    table_data.append([metric, f'{value:.4f}', f'{target:.4f}', status])

ax4.axis('tight')
ax4.axis('off')
table = ax4.table(cellText=table_data,
                  colLabels=['Metric', 'Achieved', 'Target', 'Status'],
                  cellLoc='center',
                  loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5)

# Color code the status column
for i in range(len(table_data)):
    if table_data[i][3] == 'Excellent':
        table[(i+1, 3)].set_facecolor('#90EE90')  # Light green
    elif table_data[i][3] == 'Good':
        table[(i+1, 3)].set_facecolor('#FFE4B5')  # Light yellow
    else:
        table[(i+1, 3)].set_facecolor('#FFB6C1')  # Light red

ax4.set_title('D) Performance Summary', pad=20)

plt.tight_layout()
plt.savefig('bayesian_network_analysis_fig3.png', dpi=300, bbox_inches='tight')
plt.show()

# Print statistical summary
print("="*60)
print("BAYESIAN BELIEF NETWORK PERFORMANCE ANALYSIS")
print("="*60)
print(f"Number of trials: {data['n_trials']}")
print(f"Success rate: {data['success_rate']:.3f}")
print(f"Mean accuracy: {data['mean_accuracy']:.6f} ± {data['std_accuracy']:.6f}")
print(f"Accuracy range: [{min(data['raw_accuracies']):.6f}, {max(data['raw_accuracies']):.6f}]")
print(f"Quantum efficiency: {data['quantum_efficiency']:.3f}")
print(f"ENAQT enhancement factor: {data['enaqt_enhancement_factor']:.2f}×")
print(f"Coherence time: {data['coherence_time_microseconds']:.1f} μs")
print(f"Resolution target met: {data['resolution_target_met']}")
print("\nMolecule-specific statistics:")
print(molecule_stats)

# Calculate additional statistics
shapiro_stat, shapiro_p = stats.shapiro(data['raw_accuracies'])
print(f"\nNormality test (Shapiro-Wilk): W={shapiro_stat:.4f}, p={shapiro_p:.4f}")

# Confidence intervals
ci_95 = stats.t.interval(0.95, len(data['raw_accuracies'])-1,
                        loc=data['mean_accuracy'],
                        scale=data['std_accuracy']/np.sqrt(len(data['raw_accuracies'])))
print(f"95% Confidence interval for mean: [{ci_95[0]:.6f}, {ci_95[1]:.6f}]")
print("="*60)
