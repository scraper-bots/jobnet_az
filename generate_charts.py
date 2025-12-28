#!/usr/bin/env python3
"""
JobNet.az Candidate Database Analysis
Business Intelligence Dashboard Generator
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for professional business charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 11

# Load the dataset
print("Loading candidate data...")
df = pd.read_csv('jobnet_candidates_async_20250828_155914.csv')

# Data preprocessing
print("Processing candidate profiles...")

# Calculate age from date_of_birth
df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')
current_date = pd.to_datetime('2025-08-28')
df['age'] = ((current_date - df['date_of_birth']).dt.days / 365.25).round(0)

# Gender mapping
df['gender_label'] = df['gender'].map({1: 'Male', 2: 'Female'})

# Parse experiences to count
def count_experiences(exp_str):
    try:
        exp_list = json.loads(exp_str) if pd.notna(exp_str) else []
        return len(exp_list)
    except:
        return 0

df['experience_count'] = df['experiences'].apply(count_experiences)

# Parse languages
def count_languages(lang_str):
    try:
        lang_list = json.loads(lang_str) if pd.notna(lang_str) else []
        return len(lang_list)
    except:
        return 0

df['language_count'] = df['languages'].apply(count_languages)

# Parse education
def has_education(edu_str):
    try:
        edu_list = json.loads(edu_str) if pd.notna(edu_str) else []
        return len(edu_list) > 0
    except:
        return False

df['has_education'] = df['education'].apply(has_education)

# Create output directory
import os
os.makedirs('charts', exist_ok=True)

print(f"Analyzing {len(df)} candidate profiles...")
print("Generating business intelligence visualizations...\n")

# ====================================================================
# CHART 1: Geographic Distribution of Talent Pool
# ====================================================================
print("1. Geographic talent distribution analysis...")
city_distribution = df['city_name'].value_counts().head(15)

fig, ax = plt.subplots(figsize=(14, 8))
bars = ax.barh(range(len(city_distribution)), city_distribution.values, color='#2E86AB')
ax.set_yticks(range(len(city_distribution)))
ax.set_yticklabels(city_distribution.index)
ax.set_xlabel('Number of Candidates', fontweight='bold')
ax.set_title('Top 15 Cities: Candidate Availability by Location',
             fontweight='bold', fontsize=15, pad=20)
ax.invert_yaxis()

# Add value labels
for i, (idx, value) in enumerate(city_distribution.items()):
    percentage = (value / len(df)) * 100
    ax.text(value + 2, i, f'{value} ({percentage:.1f}%)',
           va='center', fontweight='bold', fontsize=10)

plt.tight_layout()
plt.savefig('charts/01_geographic_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 2: Salary Expectations by Industry Sector
# ====================================================================
print("2. Salary expectations by industry...")
salary_by_sector = df.groupby('parent_category_name')['salary_min'].agg(['mean', 'median', 'count'])
salary_by_sector = salary_by_sector[salary_by_sector['count'] >= 5].sort_values('median', ascending=False).head(12)

fig, ax = plt.subplots(figsize=(14, 8))
x = range(len(salary_by_sector))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], salary_by_sector['mean'], width,
               label='Average Salary', color='#06A77D', alpha=0.8)
bars2 = ax.bar([i + width/2 for i in x], salary_by_sector['median'], width,
               label='Median Salary', color='#F77F00', alpha=0.8)

ax.set_ylabel('Salary Expectation (AZN)', fontweight='bold')
ax.set_title('Salary Expectations by Industry Sector (Top 12)',
             fontweight='bold', fontsize=15, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(salary_by_sector.index, rotation=45, ha='right')
ax.legend(loc='upper right')
ax.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
           f'{int(height)}', ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/02_salary_by_industry.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 3: Gender Distribution Across Top Industry Sectors
# ====================================================================
print("3. Gender diversity analysis...")
# Get top 10 sectors
top_sectors = df['parent_category_name'].value_counts().head(10).index
gender_sector = df[df['parent_category_name'].isin(top_sectors)].groupby(
    ['parent_category_name', 'gender_label']).size().unstack(fill_value=0)

fig, ax = plt.subplots(figsize=(14, 8))
gender_sector_pct = gender_sector.div(gender_sector.sum(axis=1), axis=0) * 100
gender_sector_pct = gender_sector_pct.sort_values('Female', ascending=True)

x = range(len(gender_sector_pct))
width = 0.35

bars1 = ax.barh([i - width/2 for i in x], gender_sector_pct['Male'], width,
               label='Male', color='#4A90E2', alpha=0.85)
bars2 = ax.barh([i + width/2 for i in x], gender_sector_pct['Female'], width,
               label='Female', color='#E94B3C', alpha=0.85)

ax.set_xlabel('Percentage of Candidates (%)', fontweight='bold')
ax.set_title('Gender Distribution Across Top 10 Industry Sectors',
             fontweight='bold', fontsize=15, pad=20)
ax.set_yticks(x)
ax.set_yticklabels(gender_sector_pct.index)
ax.legend(loc='lower right')
ax.grid(axis='x', alpha=0.3)

# Add percentage labels
for bars in [bars1, bars2]:
    for bar in bars:
        width_val = bar.get_width()
        ax.text(width_val + 1, bar.get_y() + bar.get_height()/2.,
               f'{width_val:.1f}%', ha='left', va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/03_gender_diversity.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 4: Candidate Engagement - Profile View Distribution
# ====================================================================
print("4. Candidate engagement metrics...")
# Create view ranges
df['view_range'] = pd.cut(df['viewed'],
                          bins=[0, 20, 50, 100, 200, df['viewed'].max()],
                          labels=['1-20', '21-50', '51-100', '101-200', '200+'])

view_distribution = df['view_range'].value_counts().sort_index()

fig, ax = plt.subplots(figsize=(12, 7))
colors = ['#D62828', '#F77F00', '#FCBF49', '#06A77D', '#2E86AB']
bars = ax.bar(range(len(view_distribution)), view_distribution.values,
             color=colors, alpha=0.85, edgecolor='black', linewidth=1.2)

ax.set_xticks(range(len(view_distribution)))
ax.set_xticklabels(view_distribution.index)
ax.set_xlabel('Number of Profile Views', fontweight='bold')
ax.set_ylabel('Number of Candidates', fontweight='bold')
ax.set_title('Candidate Profile Engagement Distribution',
             fontweight='bold', fontsize=15, pad=20)
ax.grid(axis='y', alpha=0.3)

# Add value labels
for i, bar in enumerate(bars):
    height = bar.get_height()
    percentage = (height / len(df)) * 100
    ax.text(bar.get_x() + bar.get_width()/2., height,
           f'{int(height)}\n({percentage:.1f}%)',
           ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/04_profile_engagement.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 5: Premium vs Regular Candidates - Comparative Analysis
# ====================================================================
print("5. Premium candidate analysis...")
premium_stats = pd.DataFrame({
    'Premium': [
        df[df['isPremium'] == True].shape[0],
        df[df['isPremium'] == True]['viewed'].mean(),
        df[df['isPremium'] == True]['salary_min'].mean()
    ],
    'Regular': [
        df[df['isPremium'] == False].shape[0],
        df[df['isPremium'] == False]['viewed'].mean(),
        df[df['isPremium'] == False]['salary_min'].mean()
    ]
}, index=['Total Candidates', 'Avg Profile Views', 'Avg Salary Expectation'])

fig, axes = plt.subplots(1, 3, figsize=(16, 6))

# Chart 1: Total candidates
ax1 = axes[0]
bars1 = ax1.bar(['Premium', 'Regular'], premium_stats.loc['Total Candidates'],
               color=['#06A77D', '#95A3A4'], alpha=0.85, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('Number of Candidates', fontweight='bold')
ax1.set_title('Candidate Count', fontweight='bold', fontsize=13)
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Chart 2: Average views
ax2 = axes[1]
bars2 = ax2.bar(['Premium', 'Regular'], premium_stats.loc['Avg Profile Views'],
               color=['#F77F00', '#95A3A4'], alpha=0.85, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Average Views', fontweight='bold')
ax2.set_title('Profile Visibility', fontweight='bold', fontsize=13)
for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Chart 3: Average salary
ax3 = axes[2]
bars3 = ax3.bar(['Premium', 'Regular'], premium_stats.loc['Avg Salary Expectation'],
               color=['#2E86AB', '#95A3A4'], alpha=0.85, edgecolor='black', linewidth=1.5)
ax3.set_ylabel('Average Salary (AZN)', fontweight='bold')
ax3.set_title('Salary Expectations', fontweight='bold', fontsize=13)
for bar in bars3:
    height = bar.get_height()
    if not pd.isna(height):
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.suptitle('Premium vs Regular Candidates: Performance Comparison',
            fontweight='bold', fontsize=15, y=1.02)
plt.tight_layout()
plt.savefig('charts/05_premium_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 6: Top 15 Job Categories by Demand
# ====================================================================
print("6. Job category demand analysis...")
top_categories = df['category_name'].value_counts().head(15)

fig, ax = plt.subplots(figsize=(14, 8))
colors_gradient = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_categories)))
bars = ax.barh(range(len(top_categories)), top_categories.values, color=colors_gradient)

ax.set_yticks(range(len(top_categories)))
ax.set_yticklabels(top_categories.index)
ax.set_xlabel('Number of Candidates', fontweight='bold')
ax.set_title('Top 15 Job Categories: Talent Pool by Specialization',
             fontweight='bold', fontsize=15, pad=20)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.3)

# Add value labels
for i, (idx, value) in enumerate(top_categories.items()):
    ax.text(value + 1, i, f'{value}', va='center', fontweight='bold', fontsize=10)

plt.tight_layout()
plt.savefig('charts/06_top_job_categories.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 7: Working Type Preferences
# ====================================================================
print("7. Working arrangement preferences...")
# Parse working types
def parse_working_types(wt_str):
    try:
        wt_list = json.loads(wt_str) if pd.notna(wt_str) else []
        return [wt['working_type_id'] for wt in wt_list]
    except:
        return []

# Mapping of working type IDs (based on typical patterns)
working_type_map = {
    1: 'Part-time',
    2: 'Full-time',
    3: 'Freelance',
    4: 'Contract',
    5: 'Internship',
    6: 'Temporary',
    7: 'Remote/Home-based'
}

all_working_types = []
for wt_str in df['working_types']:
    all_working_types.extend(parse_working_types(wt_str))

working_type_counts = pd.Series(all_working_types).value_counts()
working_type_labels = [working_type_map.get(wt, f'Type {wt}') for wt in working_type_counts.index]

fig, ax = plt.subplots(figsize=(12, 7))
colors = ['#2E86AB', '#06A77D', '#F77F00', '#D62828', '#A23B72', '#F18F01', '#C73E1D']
bars = ax.bar(range(len(working_type_counts)), working_type_counts.values,
             color=colors[:len(working_type_counts)], alpha=0.85,
             edgecolor='black', linewidth=1.2)

ax.set_xticks(range(len(working_type_counts)))
ax.set_xticklabels(working_type_labels, rotation=45, ha='right')
ax.set_ylabel('Number of Candidates', fontweight='bold')
ax.set_title('Candidate Preferences: Working Arrangement Types',
             fontweight='bold', fontsize=15, pad=20)
ax.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars:
    height = bar.get_height()
    percentage = (height / len(df)) * 100
    ax.text(bar.get_x() + bar.get_width()/2., height,
           f'{int(height)}\n({percentage:.1f}%)',
           ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/07_working_preferences.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 8: Age Demographics of Candidate Pool
# ====================================================================
print("8. Age demographics analysis...")
# Filter valid ages
age_data = df[df['age'].notna() & (df['age'] > 16) & (df['age'] < 70)]['age']

fig, ax = plt.subplots(figsize=(12, 7))
n, bins, patches = ax.hist(age_data, bins=20, color='#2E86AB', alpha=0.7,
                           edgecolor='black', linewidth=1.2)

# Color code by age groups
for i, patch in enumerate(patches):
    if bins[i] < 25:
        patch.set_facecolor('#06A77D')  # Young professionals
    elif bins[i] < 35:
        patch.set_facecolor('#2E86AB')  # Mid-career
    elif bins[i] < 45:
        patch.set_facecolor('#F77F00')  # Experienced
    else:
        patch.set_facecolor('#D62828')  # Senior

ax.set_xlabel('Age (Years)', fontweight='bold')
ax.set_ylabel('Number of Candidates', fontweight='bold')
ax.set_title('Age Distribution of Candidate Pool',
             fontweight='bold', fontsize=15, pad=20)
ax.grid(axis='y', alpha=0.3)

# Add statistics
mean_age = age_data.mean()
median_age = age_data.median()
ax.axvline(mean_age, color='red', linestyle='--', linewidth=2,
          label=f'Average Age: {mean_age:.1f}')
ax.axvline(median_age, color='green', linestyle='--', linewidth=2,
          label=f'Median Age: {median_age:.1f}')
ax.legend(loc='upper right', fontsize=11)

plt.tight_layout()
plt.savefig('charts/08_age_demographics.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 9: Experience Level Distribution
# ====================================================================
print("9. Experience level analysis...")
# Categorize by experience count
def categorize_experience(count):
    if count == 0:
        return 'Entry Level (No Experience)'
    elif count == 1:
        return 'Junior (1 Position)'
    elif count == 2:
        return 'Mid-Level (2 Positions)'
    elif count >= 3:
        return 'Senior (3+ Positions)'
    return 'Entry Level (No Experience)'

df['experience_level'] = df['experience_count'].apply(categorize_experience)
exp_distribution = df['experience_level'].value_counts()

# Reorder for logical flow
exp_order = ['Entry Level (No Experience)', 'Junior (1 Position)',
             'Mid-Level (2 Positions)', 'Senior (3+ Positions)']
exp_distribution = exp_distribution.reindex([e for e in exp_order if e in exp_distribution.index])

fig, ax = plt.subplots(figsize=(12, 7))
colors = ['#D62828', '#F77F00', '#06A77D', '#2E86AB']
bars = ax.bar(range(len(exp_distribution)), exp_distribution.values,
             color=colors[:len(exp_distribution)], alpha=0.85,
             edgecolor='black', linewidth=1.2)

ax.set_xticks(range(len(exp_distribution)))
ax.set_xticklabels(exp_distribution.index, rotation=20, ha='right')
ax.set_ylabel('Number of Candidates', fontweight='bold')
ax.set_title('Candidate Distribution by Experience Level',
             fontweight='bold', fontsize=15, pad=20)
ax.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars:
    height = bar.get_height()
    percentage = (height / len(df)) * 100
    ax.text(bar.get_x() + bar.get_width()/2., height,
           f'{int(height)}\n({percentage:.1f}%)',
           ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/09_experience_levels.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 10: Education Status and Language Skills
# ====================================================================
print("10. Education and language skills analysis...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# Education status
education_status = df['has_education'].value_counts()
colors_edu = ['#06A77D', '#D62828']
bars_edu = ax1.bar([0, 1],
                   [education_status.get(True, 0),
                    education_status.get(False, 0)],
                   color=colors_edu, alpha=0.85,
                   edgecolor='black', linewidth=1.2)
ax1.set_xticks([0, 1])
ax1.set_xticklabels(['With Education Info', 'Without Education Info'])
ax1.set_ylabel('Number of Candidates', fontweight='bold')
ax1.set_title('Education Information Availability', fontweight='bold', fontsize=13)
ax1.grid(axis='y', alpha=0.3)

for i, v in enumerate([education_status.get(True, 0), education_status.get(False, 0)]):
    pct = (v / len(df)) * 100
    ax1.text(i, v, f'{v}\n({pct:.1f}%)', ha='center', va='bottom',
            fontsize=11, fontweight='bold')

# Language skills
language_dist = df['language_count'].value_counts().sort_index()
colors_lang = plt.cm.Blues(np.linspace(0.4, 0.9, len(language_dist)))
bars2 = ax2.bar(language_dist.index, language_dist.values,
               color=colors_lang, alpha=0.85, edgecolor='black', linewidth=1.2)

ax2.set_xlabel('Number of Languages', fontweight='bold')
ax2.set_ylabel('Number of Candidates', fontweight='bold')
ax2.set_title('Multi-Language Proficiency', fontweight='bold', fontsize=13)
ax2.grid(axis='y', alpha=0.3)

for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.suptitle('Education and Language Capabilities', fontweight='bold', fontsize=15, y=1.00)
plt.tight_layout()
plt.savefig('charts/10_education_language.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 11: Salary Distribution Overview
# ====================================================================
print("11. Salary expectations overview...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# Salary ranges
salary_ranges = pd.cut(df['salary_min'],
                      bins=[0, 400, 600, 800, 1000, 1500, df['salary_min'].max()],
                      labels=['<400', '400-600', '600-800', '800-1000', '1000-1500', '1500+'])
salary_dist = salary_ranges.value_counts().sort_index()

colors_salary = ['#D62828', '#F77F00', '#FCBF49', '#06A77D', '#2E86AB', '#184E77']
bars1 = ax1.bar(range(len(salary_dist)), salary_dist.values,
               color=colors_salary, alpha=0.85, edgecolor='black', linewidth=1.2)
ax1.set_xticks(range(len(salary_dist)))
ax1.set_xticklabels(salary_dist.index, rotation=0)
ax1.set_xlabel('Salary Range (AZN)', fontweight='bold')
ax1.set_ylabel('Number of Candidates', fontweight='bold')
ax1.set_title('Salary Expectation Distribution', fontweight='bold', fontsize=13)
ax1.grid(axis='y', alpha=0.3)

for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Top 10 cities by average salary
city_salary = df.groupby('city_name').agg({
    'salary_min': 'mean',
    'id': 'count'
}).rename(columns={'id': 'count'})
city_salary = city_salary[city_salary['count'] >= 5].sort_values('salary_min', ascending=False).head(10)

bars2 = ax2.barh(range(len(city_salary)), city_salary['salary_min'],
                color='#2E86AB', alpha=0.85, edgecolor='black', linewidth=1.2)
ax2.set_yticks(range(len(city_salary)))
ax2.set_yticklabels(city_salary.index)
ax2.set_xlabel('Average Salary Expectation (AZN)', fontweight='bold')
ax2.set_title('Top 10 Cities by Avg Salary Expectation', fontweight='bold', fontsize=13)
ax2.invert_yaxis()
ax2.grid(axis='x', alpha=0.3)

for i, (idx, row) in enumerate(city_salary.iterrows()):
    ax2.text(row['salary_min'] + 20, i, f'{int(row["salary_min"])} AZN',
            va='center', fontsize=10, fontweight='bold')

plt.suptitle('Salary Expectations Analysis', fontweight='bold', fontsize=15, y=1.00)
plt.tight_layout()
plt.savefig('charts/11_salary_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# CHART 12: Gender Pay Gap Analysis
# ====================================================================
print("12. Gender compensation analysis...")

gender_salary = df.groupby('gender_label')['salary_min'].agg(['mean', 'median', 'count'])
gender_salary = gender_salary[gender_salary['count'] > 0]

fig, ax = plt.subplots(figsize=(12, 7))
x = range(len(gender_salary))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], gender_salary['mean'], width,
              label='Average Salary', color='#4A90E2', alpha=0.85,
              edgecolor='black', linewidth=1.2)
bars2 = ax.bar([i + width/2 for i in x], gender_salary['median'], width,
              label='Median Salary', color='#E94B3C', alpha=0.85,
              edgecolor='black', linewidth=1.2)

ax.set_ylabel('Salary Expectation (AZN)', fontweight='bold')
ax.set_title('Salary Expectations by Gender', fontweight='bold', fontsize=15, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(gender_salary.index)
ax.legend(loc='upper right', fontsize=12)
ax.grid(axis='y', alpha=0.3)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Calculate and display gap
if 'Male' in gender_salary.index and 'Female' in gender_salary.index:
    gap = gender_salary.loc['Male', 'mean'] - gender_salary.loc['Female', 'mean']
    gap_pct = (gap / gender_salary.loc['Male', 'mean']) * 100
    ax.text(0.5, max(gender_salary['mean']) * 0.95,
           f'Gender Pay Gap: {abs(gap):.0f} AZN ({abs(gap_pct):.1f}%)',
           ha='center', fontsize=12, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('charts/12_gender_pay_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ====================================================================
# Summary Statistics
# ====================================================================
print("\n" + "="*60)
print("ANALYSIS COMPLETE - KEY METRICS SUMMARY")
print("="*60)
print(f"Total Candidates Analyzed: {len(df)}")
print(f"Total Cities Represented: {df['city_name'].nunique()}")
print(f"Total Job Categories: {df['category_name'].nunique()}")
print(f"Average Salary Expectation: {df['salary_min'].mean():.0f} AZN")
print(f"Median Salary Expectation: {df['salary_min'].median():.0f} AZN")
print(f"Average Profile Views: {df['viewed'].mean():.1f}")
print(f"Premium Candidates: {df['isPremium'].sum()} ({(df['isPremium'].sum()/len(df)*100):.1f}%)")
print(f"Average Age: {age_data.mean():.1f} years")
print(f"Gender Split - Male: {(df['gender_label']=='Male').sum()} ({(df['gender_label']=='Male').sum()/len(df)*100:.1f}%)")
print(f"Gender Split - Female: {(df['gender_label']=='Female').sum()} ({(df['gender_label']=='Female').sum()/len(df)*100:.1f}%)")
print("="*60)
print("\nAll charts saved to 'charts/' directory")
print("Total charts generated: 12")
print("\nReady for business presentation!")
