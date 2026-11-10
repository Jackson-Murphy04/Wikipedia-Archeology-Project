"""Generate the eight step notebooks listed in anlysisPlan.txt."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.splitlines(keepends=True)}

def notebook(title, intro, cells):
    doc = [md(f"# {title}\n\n{intro}\n\nRun cells from top to bottom. Shared helpers and file paths are in `analysis_common.py`. Outputs go to `analysis_results/` and `figures/`."), *cells]
    obj = {"cells": doc, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}}, "nbformat": 4, "nbformat_minor": 5}
    path = ROOT / (title.split(" — ")[0].replace(" ", "_").lower() + ".ipynb")
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(path.name)

common = "from pathlib import Path\nimport sys\nfrom IPython.display import display\nROOT = Path.cwd().resolve()\nwhile not (ROOT / 'analysis' / 'analysis_common.py').exists() and ROOT.parent != ROOT: ROOT = ROOT.parent\nsys.path.insert(0, str(ROOT / 'analysis'))\nfrom analysis_common import *\n"

notebook("step01_dataset_validation — Dataset Overview and Validation", "Establish scope, completeness, ordering, and article coverage before interpreting patterns.", [
    code(common + "df = load_revisions()\nvalid = df.dropna(subset=['timestamp'])\narticle_counts = df.groupby('article_title').size().sort_values(ascending=False)\nsummary = pd.DataFrame([{'revision_records': len(df), 'articles': df.article_title.nunique(), 'unique_nonempty_usernames': df.username.nunique(dropna=True), 'mean_revisions_per_article': article_counts.mean(), 'median_revisions_per_article': article_counts.median(), 'earliest_timestamp_utc': valid.timestamp.min(), 'latest_timestamp_utc': valid.timestamp.max(), 'coverage_days': (valid.timestamp.max()-valid.timestamp.min()).total_seconds()/86400, 'invalid_timestamp_rows': df.timestamp.isna().sum()}])\ndisplay(summary.T.rename(columns={0:'value'}))\nsave_table(summary, 'step01_dataset_summary.csv')\n"),
    code("fields = ['timestamp','revision_id','username','edit_comment','article_size_bytes']\nmissing_masks={'timestamp':df.timestamp.isna(),'revision_id':df.revision_id.isna(),'username':df.username_missing,'edit_comment':df.comment_missing,'article_size_bytes':df.article_size_bytes.isna()}\nmissing = pd.DataFrame({'field': fields, 'missing_count': [int(missing_masks[c].sum()) for c in fields]})\nmissing['missing_percent'] = 100 * missing.missing_count / len(df)\nmissing['nonempty_percent'] = 100 - missing.missing_percent\narticle_missing = pd.concat([df[['article_title']],pd.DataFrame({c:missing_masks[c] for c in fields})],axis=1).groupby('article_title').mean().mul(100).add_suffix('_missing_pct').reset_index()\nquality = pd.DataFrame([{'duplicate_revision_ids': int(df.revision_id.duplicated(keep=False).sum()), 'duplicate_rows_after_first': int(df.revision_id.duplicated().sum()), 'unparseable_timestamps': int(df.timestamp.isna().sum()), 'negative_sizes': int((df.article_size_bytes < 0).sum()), 'missing_size_values': int(df.article_size_bytes.isna().sum()), 'missing_revision_ids': int(df.revision_id.isna().sum()), 'missing_parent_ids': int(df.parent_id.isna().sum()), 'rows_out_of_chronological_order_within_article': int((df.groupby('article_title', sort=False).timestamp.apply(lambda s: s.dropna().diff().lt(pd.Timedelta(0)).sum())).sum()), 'timestamp_duplicates': int(df.duplicated(['article_title','timestamp','revision_id']).sum())}])\ndisplay(missing); display(quality.T); display(article_missing.sort_values('timestamp_missing_pct', ascending=False).head(10))\nsave_table(missing, 'step01_field_completeness.csv'); save_table(article_missing, 'step01_article_completeness.csv'); save_table(quality, 'step01_validation_report.csv')"),
    code("coverage = article_counts.rename('revisions').reset_index()\ncoverage['share_of_records_pct'] = 100*coverage.revisions/len(df)\ncoverage['cumulative_share_pct'] = coverage.share_of_records_pct.cumsum()\ncoverage.to_csv(OUTPUT_DIR/'step01_article_coverage.csv', index=False)\ndisplay(coverage)\nfig, ax = plt.subplots(figsize=(12,8)); coverage.sort_values('revisions').plot.barh(x='article_title',y='revisions',ax=ax,legend=False,color='#3569a8'); ax.set(title='Revision coverage by article',xlabel='Revision records',ylabel='Article'); finish_plot(fig,'step01_article_coverage.png')\n"),
]),

notebook("step02_temporal_patterns — Temporal Editing Patterns", "Measure annual and monthly activity, detect article-specific spikes, and document the limits on explaining them.", [
    code(common + "df = load_revisions()\nmonthly = monthly_activity(df)\nmonthly['year'] = monthly.timestamp.dt.year\nmonthly['month'] = monthly.timestamp.dt.month\nannual = df.dropna(subset=['timestamp']).groupby([df.timestamp.dt.year.rename('year'),'article_title']).size().rename('revisions').reset_index()\noverall_annual = annual.groupby('year',as_index=False).revisions.sum()\nsave_table(monthly,'step02_monthly_activity_by_article.csv'); save_table(annual,'step02_annual_activity_by_article.csv'); save_table(overall_annual,'step02_annual_activity.csv')\ndisplay(overall_annual.tail(20))\nfig, ax=plt.subplots(figsize=(14,5)); ax.plot(overall_annual.year,overall_annual.revisions,color='#315c9b'); ax.set(title='Annual revision activity',xlabel='Year',ylabel='Revision records'); ax.grid(alpha=.25); finish_plot(fig,'step02_annual_activity.png')\noverall_monthly = monthly.groupby('timestamp',as_index=False).revisions.sum()\nfig, ax=plt.subplots(figsize=(14,5)); ax.plot(overall_monthly.timestamp,overall_monthly.revisions,lw=.8,alpha=.65); ax.plot(overall_monthly.timestamp,overall_monthly.revisions.rolling(12,min_periods=1).mean(),lw=2,label='12-month mean'); ax.set(title='Monthly revision activity',xlabel='Month',ylabel='Revision records'); ax.legend(); ax.grid(alpha=.25); finish_plot(fig,'step02_monthly_activity.png')\n"),
    code("spikes = robust_spikes(monthly).sort_values(['is_spike','revisions'],ascending=[False,False])\nspikes.to_csv(OUTPUT_DIR/'step02_article_monthly_spikes.csv',index=False)\ndisplay(spikes[spikes.is_spike].head(30))\n# Compare article start-to-end activity using first and last calendar-year counts.\nannual_by_article = annual.sort_values(['article_title','year'])\ntrend_rows=[]\nfor article,g in annual_by_article.groupby('article_title'):\n    first,last=g.iloc[0],g.iloc[-1]\n    trend_rows.append({'article_title':article,'first_observed_year':int(first.year),'last_observed_year':int(last.year),'first_year_revisions':int(first.revisions),'last_year_revisions':int(last.revisions),'first_vs_last_year_ratio':(last.revisions/first.revisions if first.revisions else np.nan),'observed_years':int(g.year.nunique())})\ntrends=pd.DataFrame(trend_rows).sort_values('observed_years',ascending=False)\nsave_table(trends,'step02_long_term_trends.csv'); display(trends)\n"),
    md("## Context investigation\n\nThe spike table is a statistical screen, not an explanation. Select candidate rows above, then record external research here. Do not describe an anniversary or current event as the cause unless an independent, dated source supports the connection. The CSV below deliberately marks context as unverified until a source is added."),
    code("context = spikes[spikes.is_spike].nlargest(20,'revisions')[['article_title','timestamp','revisions','article_median','robust_threshold']].copy()\ncontext['context_claim']=''\ncontext['source_title']=''\ncontext['source_url']=''\ncontext['source_date']=''\ncontext['assessment']='Uninvestigated; correlation does not establish cause'\nsave_table(context,'step02_spike_context_review.csv'); display(context)\n"),
]),

notebook("step03_article_growth — Article Growth and Structural Evolution", "Quantify observed page-size changes and flag candidate revisions for content-level follow-up.", [
    code(common + "df=load_revisions().dropna(subset=['timestamp','article_size_bytes']).sort_values(['article_title','timestamp','revision_id'])\ngrowth_rows=[]\nfor article,g in df.groupby('article_title'):\n    first,last=g.iloc[0],g.iloc[-1]; net=float(last.article_size_bytes-first.article_size_bytes)\n    years=(last.timestamp-first.timestamp).total_seconds()/(365.2425*86400)\n    growth_rows.append({'article_title':article,'first_timestamp':first.timestamp,'first_size_bytes':first.article_size_bytes,'first_revision_id':first.revision_id,'last_timestamp':last.timestamp,'last_size_bytes':last.article_size_bytes,'last_revision_id':last.revision_id,'net_change_bytes':net,'growth_pct':100*net/first.article_size_bytes if first.article_size_bytes else np.nan,'average_annual_net_change_bytes':net/years if years>0 else np.nan,'observed_span_years':years,'revision_records':len(g)})\ngrowth=pd.DataFrame(growth_rows).sort_values('net_change_bytes',ascending=False)\nsave_table(growth,'step03_article_growth.csv'); display(growth)\nfig,ax=plt.subplots(figsize=(12,8)); growth.sort_values('net_change_bytes').plot.barh(x='article_title',y='net_change_bytes',ax=ax,legend=False,color='#579d74'); ax.axvline(0,color='black',lw=.7); ax.set(title='Net observed article size change',xlabel='Bytes (last observed minus first observed)',ylabel='Article'); finish_plot(fig,'step03_net_growth.png')\n"),
    code("# Timeline samples use the observed revision metadata; the dataset may be sampled, so lines represent collected observations.\ntop=growth.nlargest(8,'net_change_bytes').article_title.tolist(); fig,ax=plt.subplots(figsize=(13,6))\nfor article in top:\n    g=df[df.article_title.eq(article)]; ax.plot(g.timestamp,g.article_size_bytes/1000,label=article,lw=1)\nax.set(title='Observed article size over time (largest net growth)',xlabel='Timestamp',ylabel='Observed size (KB)'); ax.legend(fontsize=8,ncol=2); ax.grid(alpha=.25); finish_plot(fig,'step03_size_over_time.png')\nchanges=df.dropna(subset=['size_change_bytes']).copy()\nlarge=changes.reindex(changes.size_change_bytes.abs().sort_values(ascending=False).index).head(100).copy()\nlarge['change_direction']=np.where(large.size_change_bytes>0,'increase','decrease')\nlarge=large[['article_title','timestamp','revision_id','parent_id','username','edit_comment','article_size_bytes','size_change_bytes','change_direction']]\nsave_table(large,'step03_largest_size_changes.csv'); display(large.head(30))\nfig,ax=plt.subplots(figsize=(10,5)); ax.hist(changes.size_change_bytes.clip(-50000,50000),bins=80,color='#8b6ca8'); ax.set(title='Consecutive observed size differences (clipped at ±50 KB)',xlabel='Bytes',ylabel='Revision transitions'); finish_plot(fig,'step03_size_change_distribution.png')\n"),
    md("## Content-level interpretation boundary\n\nA size difference does not identify which paragraphs, claims, citations, or sections changed. The revision IDs and parent IDs in `step03_largest_size_changes.csv` are reproducible candidates for Step 5. Do not call these structural reorganizations until a revision diff has been inspected."),
]),

notebook("step04_editor_participation — Editor Participation and Behavior", "Measure contributor participation, account-type proxies, concentration, and minor-edit patterns.", [
    code(common + "df=classify_editors(load_revisions())\nper_article=[]\nfor article,g in df.groupby('article_title'):\n    named=g.username.dropna(); counts=named.value_counts(); top=counts.head(10)\n    per_article.append({'article_title':article,'revisions':len(g),'unique_usernames':named.nunique(),'unique_positive_user_ids':g.loc[g.user_id.gt(0),'user_id'].nunique(),'anonymous_revisions':int(g.editor_type.eq('Anonymous (user ID 0)').sum()),'registered_revisions':int(g.editor_type.eq('Registered (positive user ID)').sum()),'unknown_identity_revisions':int(g.editor_type.eq('Unknown / unavailable').sum()),'anonymous_pct':100*g.editor_type.eq('Anonymous (user ID 0)').mean(),'registered_pct':100*g.editor_type.eq('Registered (positive user ID)').mean(),'minor_pct':100*g.is_minor.mean(),'top1_revision_share_pct':100*top.head(1).sum()/len(g),'top5_revision_share_pct':100*top.head(5).sum()/len(g),'top10_revision_share_pct':100*top.sum()/len(g),'username_gini':gini(counts.values)})\narticle_stats=pd.DataFrame(per_article).sort_values('revisions',ascending=False); save_table(article_stats,'step04_article_editor_metrics.csv'); display(article_stats)\n"),
    code("editor_counts=df.groupby(['username','editor_type'],dropna=False).size().rename('revisions').reset_index().sort_values('revisions',ascending=False)\n# Export top contributors without inferring identity or motive.\ntop=editor_counts.head(100); save_table(top,'step04_top_contributors.csv')\nidentity=df.editor_type.value_counts().rename_axis('editor_type').reset_index(name='revisions'); identity['share_pct']=100*identity.revisions/len(df); save_table(identity,'step04_editor_type_summary.csv'); display(identity)\nfig,ax=plt.subplots(figsize=(8,5)); ax.bar(identity.editor_type,identity.share_pct,color=['#4c78a8','#f58518','#9d9d9d']); ax.set(title='Revision records by contributor metadata class',ylabel='Share of revisions (%)'); ax.tick_params(axis='x',rotation=15); finish_plot(fig,'step04_editor_types.png')\nconcentration=article_stats.set_index('article_title')[['top1_revision_share_pct','top5_revision_share_pct','top10_revision_share_pct']].sort_values('top10_revision_share_pct'); fig,ax=plt.subplots(figsize=(11,8)); concentration.plot.barh(ax=ax); ax.set(title='Revision share from top contributors by article',xlabel='Share of article revisions (%)'); finish_plot(fig,'step04_contributor_concentration.png')\n"),
    code("minor=(df.groupby('article_title').agg(revisions=('revision_id','size'),minor_revisions=('is_minor','sum'),minor_pct=('is_minor',lambda s:100*s.mean()),unique_editors=('username','nunique')).reset_index().sort_values('minor_pct',ascending=False)); save_table(minor,'step04_minor_edit_comparison.csv'); display(minor)\nfig,ax=plt.subplots(figsize=(9,5)); ax.scatter(minor.revisions,minor.minor_pct); ax.set(title='Article activity and minor-edit share',xlabel='Revision records',ylabel='Minor edits (%)'); finish_plot(fig,'step04_minor_vs_activity.png')\n"),
    md("## Interpretation notes\n\n`user_id == 0` is treated as anonymous, positive IDs as registered, and missing IDs as unavailable. Username strings are not proof of a real-world identity. The Gini coefficient summarizes the distribution of revision counts across usernames within each article; it is not a measure of contributor quality."),
]),

notebook("step05_significant_revisions — Significant Revision Events and Content Changes", "Build a reproducible candidate sample and retrieve parent/revision diffs where network access permits.", [
    code(common + "df=load_revisions().sort_values(['article_title','timestamp','revision_id'])\nmonthly=monthly_activity(df); spikes=robust_spikes(monthly); spike_rows=spikes[spikes.is_spike].nlargest(12,'revisions')\nsize_rows=df.dropna(subset=['size_change_bytes']).reindex(df.dropna(subset=['size_change_bytes']).size_change_bytes.abs().nlargest(12).index)\nrevert_mask=df.edit_comment.str.contains(r'\\b(revert|reverted|undo|undid|rollback|rvv?)\\b',case=False,regex=True,na=False)\ncomment_rows=df[revert_mask].nlargest(8,'revision_id')\n# Stratified sample: large size change, high-spike months, comment/revert signals, early and recent dates.\ncandidates=pd.concat([size_rows,comment_rows,df[df.article_title.isin(spike_rows.article_title)].groupby('article_title',group_keys=False).tail(2),df.groupby('article_title',group_keys=False).head(1),df.groupby('article_title',group_keys=False).tail(1)]).drop_duplicates('revision_id').dropna(subset=['revision_id','parent_id'])\ncandidates=candidates.sort_values('size_change_bytes',key=lambda x:x.abs(),ascending=False).drop_duplicates('article_title').head(30).copy()\ncandidates['candidate_reason']=np.select([candidates.edit_comment.str.contains(r'\\b(revert|undo|rollback|rv)\\b',case=False,regex=True),candidates.size_change_bytes.abs().ge(10000)],[ 'Edit summary suggests revert; verify diff','Large observed byte change'],default='Stratified temporal/activity sample')\ncols=['article_title','timestamp','revision_id','parent_id','username','edit_comment','article_size_bytes','size_change_bytes','candidate_reason']\nsave_table(candidates[cols],'step05_significant_revision_candidates.csv'); display(candidates[cols])\n"),
    code("# Retrieval is attempted only for a small, diverse sample. API responses are stored with IDs for auditability.\nimport requests, time, html\nAPI='https://en.wikipedia.org/w/api.php'\nretrieved=[]; network_available=True\nfor row in candidates.head(8).itertuples():\n    rec={'article_title':row.article_title,'timestamp':str(row.timestamp),'revision_id':int(row.revision_id),'parent_id':int(row.parent_id),'edit_comment':row.edit_comment,'size_change_bytes':row.size_change_bytes,'retrieval_status':'not attempted','diff_html':''}\n    if not network_available: rec['retrieval_status']='skipped after network/API failure on earlier request'\n    else:\n        try:\n            response=requests.get(API,params={'action':'query','prop':'compare','fromrev':rec['parent_id'],'torev':rec['revision_id'],'format':'json','formatversion':2},headers={'User-Agent':'WikipediaDigitalArchaeologyResearch/1.0 (educational analysis)'},timeout=5)\n            response.raise_for_status(); payload=response.json(); comp=payload.get('compare',{})\n            if comp.get('body') is not None: rec['diff_html']=comp['body']; rec['retrieval_status']='retrieved'\n            else: rec['retrieval_status']='API returned no diff: '+str(payload.get('errors',payload))[:400]\n        except Exception as exc: rec['retrieval_status']=f'retrieval failed: {type(exc).__name__}: {exc}'; network_available=False\n    retrieved.append(rec); time.sleep(.15)\ndiffs=pd.DataFrame(retrieved); save_table(diffs,'step05_revision_diffs_raw.csv'); display(diffs[['article_title','timestamp','revision_id','parent_id','retrieval_status']])\n"),
    code("# Strip HTML tags for a compact, reviewable text excerpt; keep raw HTML in the companion CSV.\nimport re\ndef plain_diff(s):\n    s=re.sub(r'<\\s*br\\s*/?>','\\n',s,flags=re.I); s=re.sub(r'<[^>]+>',' ',s); return html.unescape(re.sub(r'\\s+',' ',s)).strip()\nexamples=diffs.copy(); examples['diff_excerpt']=examples.diff_html.map(plain_diff).str.slice(0,2500)\nexamples['change_classification']='Requires human review; diff excerpt alone does not establish historical significance'\nexamples['reviewer_notes']=''\nsave_table(examples.drop(columns='diff_html'),'step05_revision_case_studies.csv'); display(examples[['article_title','revision_id','parent_id','retrieval_status','diff_excerpt']].head(10))\n"),
    md("## Classification and evidence\n\nInspect the rendered diff excerpts and raw API HTML before assigning categories such as additions, removals, framing changes, references, or reverts. The retrieval cell records failures (for example, revision visibility or network restrictions) instead of fabricating content. Edit summaries are leads, not verified descriptions. A proposed revert is verified only when the diff supports it. The case-study table has a reviewer-notes column for documented examples."),
]),

notebook("step06_category_comparison — Historical Event Category Comparison", "Compare the 31 article pages using one documented primary category per article.", [
    code(common + "df=classify_editors(load_revisions()).sort_values(['article_title','timestamp','revision_id'])\ncategory=pd.DataFrame({'article_title':list(category_map()),'primary_category':list(category_map().values())})\narticle=[]\nfor title,g in df.groupby('article_title'):\n    g=g.dropna(subset=['timestamp','article_size_bytes']); first,last=(g.iloc[0],g.iloc[-1]) if len(g) else (None,None)\n    years=(last.timestamp-first.timestamp).total_seconds()/(365.2425*86400) if len(g)>1 else np.nan\n    counts=g.username.value_counts()\n    article.append({'article_title':title,'revisions':len(g),'unique_editors':g.username.nunique(),'avg_revisions_per_observed_year':len(g)/years if years and years>0 else np.nan,'first_size':first.article_size_bytes if first is not None else np.nan,'last_size':last.article_size_bytes if last is not None else np.nan,'growth_pct':100*(last.article_size_bytes-first.article_size_bytes)/first.article_size_bytes if first is not None and first.article_size_bytes else np.nan,'registered_pct':100*g.editor_type.eq('Registered (positive user ID)').mean(),'anonymous_pct':100*g.editor_type.eq('Anonymous (user ID 0)').mean(),'top10_share_pct':100*counts.head(10).sum()/len(g),'minor_pct':100*g.is_minor.mean()})\narticle=pd.DataFrame(article).merge(category,on='article_title',how='left',validate='one_to_one')\nassert article.primary_category.notna().all(), 'Every analyzed article needs a primary category.'\nsave_table(category,'step06_article_category_mapping.csv'); save_table(article,'step06_article_category_metrics.csv'); display(category)\n"),
    code("category_summary=article.groupby('primary_category').agg(articles=('article_title','nunique'),total_revisions=('revisions','sum'),median_revisions_per_article=('revisions','median'),mean_revisions_per_article=('revisions','mean'),median_revisions_per_year=('avg_revisions_per_observed_year','median'),median_unique_editors=('unique_editors','median'),median_growth_pct=('growth_pct','median'),median_registered_pct=('registered_pct','median'),median_anonymous_pct=('anonymous_pct','median'),median_top10_share_pct=('top10_share_pct','median'),median_minor_pct=('minor_pct','median')).reset_index().sort_values('articles',ascending=False)\nsave_table(category_summary,'step06_category_summary.csv'); display(category_summary)\nfig,ax=plt.subplots(figsize=(11,6)); category_summary.sort_values('median_revisions_per_article').plot.barh(x='primary_category',y='median_revisions_per_article',ax=ax,legend=False,color='#4f8d88'); ax.set(title='Median revisions per article by primary event category',xlabel='Median revision records',ylabel='Primary category'); finish_plot(fig,'step06_category_activity.png')\nfig,ax=plt.subplots(figsize=(11,6)); article.boxplot(column='growth_pct',by='primary_category',ax=ax,rot=20); ax.set(title='Observed article growth by primary category',xlabel='Primary category',ylabel='Net size change (%)'); fig.suptitle(''); finish_plot(fig,'step06_category_growth.png')\n"),
    md("## Interpretation\n\nPrimary categories are a documented, mutually exclusive convenience for comparison; several articles could reasonably fit elsewhere. Always show article counts and medians because category sizes differ and a few articles can dominate means. Category-level differences are descriptive and do not establish that category caused editing behavior."),
]),

notebook("step07_synthesis — Synthesize Findings and Answer Research Questions", "Bring the previous outputs together and state what the metadata can and cannot support.", [
    code(common + "df=load_revisions()\nsummary=pd.read_csv(OUTPUT_DIR/'step01_dataset_summary.csv').iloc[0]\ngrowth=pd.read_csv(OUTPUT_DIR/'step03_article_growth.csv')\neditors=pd.read_csv(OUTPUT_DIR/'step04_article_editor_metrics.csv')\ncategories=pd.read_csv(OUTPUT_DIR/'step06_category_summary.csv')\nspikes=pd.read_csv(OUTPUT_DIR/'step02_article_monthly_spikes.csv')\nvalid_spikes=spikes[spikes.is_spike].sort_values('revisions',ascending=False).head(10)\nfindings=[\n('Dataset scale',f\"{int(summary.revision_records):,} revision records cover {int(summary.articles)} articles; median {summary.median_revisions_per_article:,.0f} records per article.\"),\n('Time coverage',f\"Valid timestamps span {summary.earliest_timestamp_utc} through {summary.latest_timestamp_utc} ({summary.coverage_days/365.2425:.1f} years).\"),\n('Article growth',f\"The largest net observed byte increase is {growth.iloc[0].article_title} (+{growth.iloc[0].net_change_bytes:,.0f} bytes); byte size is a proxy, not a measure of historical completeness.\"),\n('Contributor concentration',f\"Median top-10 username revision share across articles is {editors.top10_revision_share_pct.median():.1f}%. Usernames and metadata do not establish identity or expertise.\"),\n('Event-category comparison',f\"Category medians describe the articles assigned to each primary category; category sample sizes range from {int(categories.articles.min())} to {int(categories.articles.max())}.\"),\n('Editing spikes','Per-article robust monthly outliers are listed in step02_article_monthly_spikes.csv. A spike is an observed anomaly, not evidence of its cause.'),\n('Content changes','Detailed claims about added/removed historical information require successful Step 5 revision diff retrieval and human inspection; metadata alone cannot answer this question.')\n]\nfor label,text in findings: print(f'\\n{label}: {text}')\n"),
    code("questions=pd.DataFrame([{'research_question':'How does coverage of historical events evolve over time?','answer':'Describe observed revision timelines and article byte-size trajectories; the collected records may be incomplete or sampled.','evidence':'step02_monthly_activity_by_article.csv; step03_article_growth.csv','confidence':'Descriptive'}, {'research_question':'When do substantial changes occur?','answer':'Use per-article monthly robust outliers and large observed byte changes; these are candidate events.','evidence':'step02_article_monthly_spikes.csv; step03_largest_size_changes.csv','confidence':'Descriptive'}, {'research_question':'Do spikes coincide with public attention or related events?','answer':'Not established by revision metadata. Requires independently dated external sources for each spike.','evidence':'step02_spike_context_review.csv','confidence':'Unverified'}, {'research_question':'What kinds of changes are made to historical information?','answer':'Only after inspecting retrieved before-and-after diffs; edit summaries and byte deltas are insufficient.','evidence':'step05_revision_case_studies.csv','confidence':'Depends on retrieval and manual review'}, {'research_question':'Do patterns differ between event types?','answer':'Compare category medians and distributions while accounting for category/article counts.','evidence':'step06_category_summary.csv','confidence':'Descriptive; mapping-sensitive'}])\nsave_table(questions,'step07_research_question_answers.csv'); display(questions)\n(OUTPUT_DIR/'step07_findings_summary.md').write_text('# Findings summary\\n\\n'+'\\n'.join(f'## {label}\\n\\n{text}\\n' for label,text in findings)+'\\n## Limitations\\n\\nRevision metadata does not encode the complete article text, reliably explain editing motivation, or establish contributor identity. Contextual claims need independent dated sources. Categories are researcher-assigned.\\n',encoding='utf-8')\n"),
    md("## Chart selection for the report\n\nRecommended core visuals: annual revision activity (Step 2), net article growth and selected size timelines (Step 3), contributor concentration and account-type proxy (Step 4), verified before/after diffs only where retrieval succeeded (Step 5), and category medians with sample counts (Step 6). Exclude any chart that does not answer a research question."),
]),

notebook("step08_artifacts_report — Reproducibility and Final Report", "Record how to recreate the analysis and assemble a report draft grounded in the generated artifacts.", [
    code(common + "# Inventory expected analysis artifacts and record reproducibility settings.\nmanifest=[]\nfor folder in [OUTPUT_DIR,FIGURES_DIR]:\n    for p in sorted(folder.glob('*')):\n        if p.is_file(): manifest.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'modified_utc':pd.Timestamp(p.stat().st_mtime,unit='s',tz='UTC')})\nmanifest=pd.DataFrame(manifest); save_table(manifest,'step08_artifact_manifest.csv'); display(manifest)\nrequirements='''Python 3.10+\\npandas\\nnumpy\\nmatplotlib\\nrequests (Step 5 diff retrieval)\\nJupyter Notebook or JupyterLab\\n'''\n(OUTPUT_DIR/'requirements-analysis.txt').write_text(requirements,encoding='utf-8')\n"),
    md("## Reproduction instructions\n\n1. Keep `historical_analysis/cleaned/historical_revisions_cleaned.csv` in place.\n2. Install the packages listed in `analysis_results/requirements-analysis.txt`.\n3. Open this project directory as the working directory.\n4. Run `step01_dataset_validation.ipynb` through `step08_artifacts_report.ipynb` in order.\n5. Review retrieval failures in Step 5 and add source citations to the Step 2 context review before making causal claims.\n6. Generated tables are written to `analysis/analysis_results`; figures are written to `analysis/figures`.\n\nThe original plan requests a 6–8 page report and team contributions. Those require human-provided repository link and team-member contribution details, so this notebook creates a report draft with explicit fill-in fields instead of inventing them."),
    code("# Draft report text from the plan's required headings and recorded findings.\nsummary=pd.read_csv(OUTPUT_DIR/'step01_dataset_summary.csv').iloc[0]\nfindings=(OUTPUT_DIR/'step07_findings_summary.md').read_text(encoding='utf-8')\nreport=f'''# Wikipedia Digital Archaeology Project — Report Draft\\n\\n## Objective and Motivation\\nThis project studies how Wikipedia articles documenting major historical events evolve, when editing activity changes, how participation is distributed, and what revision patterns can reveal.\\n\\n## Data and Data Collection\\nThe analysis uses the cleaned revision metadata at `historical_analysis/cleaned/historical_revisions_cleaned.csv`. It contains {int(summary.revision_records):,} revision records across {int(summary.articles)} articles. Collection details should be checked against the project collection script before submission.\\n\\n## Data Processing and Quality\\nTimestamps are parsed as UTC, numeric identifiers and article sizes are normalized, and revisions are ordered within article by timestamp and revision ID. See `step01_validation_report.csv` and `step01_field_completeness.csv` for observed quality metrics.\\n\\n## Methods or Implementation\\nThe notebooks calculate per-period activity, robust monthly outliers (median + 3 × 1.4826 × MAD per article), first-to-last observed article-size change, contributor participation and concentration, and category summaries using documented primary categories. Revision diffs are retrieved only for a selected sample.\\n\\n## Results\\n{findings}\\n\\n## Problems, Limitations, and Interpretation\\nThe dataset is metadata rather than the full text of every revision. Anomaly detection identifies candidate periods but cannot explain their causes. Article byte counts include formatting, references, and other non-prose. Usernames and user IDs do not establish identity, expertise, or reliability. Category assignments are researcher-defined and results are sensitive to the mapping and article mix.\\n\\n## Future Work\\nComplete manual review of retrieved diffs, investigate selected spikes with independent dated sources, verify the collection process and sampling, and refine the category mapping with project collaborators.\\n\\n## Team Contributions\\n[Add each team member and their verified contribution.]\\n\\n## Repository\\n[Insert the final repository link.]\\n'''\n(OUTPUT_DIR/'final_report_draft.md').write_text(report,encoding='utf-8'); print('Wrote',OUTPUT_DIR/'final_report_draft.md')\n"),
])

def append_code(path, source):
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["cells"].append(code(source))
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

append_code(ROOT / "step01_dataset_validation.ipynb", """# Parent-link integrity and unusually large size values need separate review.
revision_lookup = df.dropna(subset=['revision_id']).drop_duplicates('revision_id').set_index('revision_id')
parents = df.dropna(subset=['parent_id']).copy()
parents['parent_in_collection'] = parents.parent_id.isin(revision_lookup.index)
parents['parent_same_article'] = parents.parent_id.map(revision_lookup.article_title).eq(parents.article_title)
parents['parent_timestamp'] = parents.parent_id.map(revision_lookup.timestamp)
parents['parent_not_earlier'] = parents.parent_timestamp.notna() & (parents.parent_timestamp >= parents.timestamp)
parent_integrity = pd.DataFrame([{'records_with_parent_id': len(parents), 'parent_not_in_collected_dataset': int((~parents.parent_in_collection).sum()), 'parent_belongs_to_another_article': int((~parents.parent_same_article & parents.parent_in_collection).sum()), 'parent_timestamp_not_earlier_than_child': int(parents.parent_not_earlier.sum())}])
extreme_sizes = df.nlargest(25, 'article_size_bytes')[['article_title','timestamp','revision_id','parent_id','article_size_bytes','edit_comment']]
parent_anomalies = parents[(~parents.parent_in_collection) | parents.parent_not_earlier][['article_title','timestamp','revision_id','parent_id','parent_timestamp','parent_in_collection','parent_not_earlier','edit_comment']]
save_table(parent_integrity, 'step01_parent_link_validation.csv'); save_table(parent_anomalies, 'step01_parent_link_anomalies.csv'); save_table(extreme_sizes, 'step01_largest_observed_sizes.csv')
display(parent_integrity); display(parent_anomalies.head(20)); display(extreme_sizes.head(10))
""")

append_code(ROOT / "step02_temporal_patterns.ipynb", """# Add one independently sourced contextual example without treating it as causal proof.
candidate = spikes[(spikes.article_title.eq('Arab Spring')) & pd.to_datetime(spikes.timestamp).dt.strftime('%Y-%m').eq('2011-02')]
if not candidate.empty:
    record = candidate.nlargest(1, 'revisions')[['article_title','timestamp','revisions','article_median','robust_threshold']].iloc[0].to_dict()
    record.update({'context_claim':'The 2011 wave of protests is documented in historical timelines; February included key developments in Egypt. This is contemporaneous context, not proof that protests caused the Wikipedia spike.', 'source_title':'EU Institute for Security Studies, Timeline 2011', 'source_url':'https://www.iss.europa.eu/sites/default/files/3.1__Timeline_2011.pdf', 'source_date':'2011 timeline', 'assessment':'Temporal context independently documented; causal relationship unproven'})
    context = pd.concat([context[~((context.article_title.eq('Arab Spring')) & pd.to_datetime(context.timestamp).dt.strftime('%Y-%m').eq('2011-02'))], pd.DataFrame([record])], ignore_index=True)
save_table(context, 'step02_spike_context_review.csv'); display(context[context.source_url.ne('')])
""")

append_code(ROOT / "step04_editor_participation.ipynb", """# The supplied minor-edit flag is constant in this dataset, so it cannot support comparisons.
minor_values = df.is_minor.value_counts(dropna=False)
print('is_minor values in cleaned input:', minor_values.to_dict())
if df.is_minor.nunique(dropna=False) == 1:
    print('Caution: the flag has no variation; minor-edit rates are 100% for every article and category and are not analytically discriminating.')
""")

append_code(ROOT / "step06_category_comparison.ipynb", """if article.minor_pct.nunique(dropna=False) <= 1:
    print('Minor-edit comparison is uninformative: the cleaned is_minor field is constant across all records.')
print('Category mapping counts:', category.groupby('primary_category').size().to_dict())
""")

append_code(ROOT / "step08_artifacts_report.ipynb", """# Expand the report draft with observed results, evidence tables, and explicit limits.
summary = pd.read_csv(OUTPUT_DIR/'step01_dataset_summary.csv').iloc[0]
coverage = pd.read_csv(OUTPUT_DIR/'step01_article_coverage.csv')
missing = pd.read_csv(OUTPUT_DIR/'step01_field_completeness.csv')
parents = pd.read_csv(OUTPUT_DIR/'step01_parent_link_validation.csv').iloc[0]
growth = pd.read_csv(OUTPUT_DIR/'step03_article_growth.csv')
editor_types = pd.read_csv(OUTPUT_DIR/'step04_editor_type_summary.csv')
editor_metrics = pd.read_csv(OUTPUT_DIR/'step04_article_editor_metrics.csv')
category_summary = pd.read_csv(OUTPUT_DIR/'step06_category_summary.csv')
spikes = pd.read_csv(OUTPUT_DIR/'step02_article_monthly_spikes.csv')
spikes = spikes[spikes.is_spike].sort_values('revisions', ascending=False)
context = pd.read_csv(OUTPUT_DIR/'step02_spike_context_review.csv')
diff_status = pd.read_csv(OUTPUT_DIR/'step05_revision_diffs_raw.csv')
case_studies = pd.read_csv(OUTPUT_DIR/'step05_revision_case_studies.csv')
second_revert_status = diff_status.loc[diff_status.revision_id.eq(30587594),'retrieval_status']
if not second_revert_status.empty and second_revert_status.iloc[0] == 'retrieved':
    second_revert_note = 'Revision 30587594 also has a retrieved diff that removes the repeated insertion about six seconds later.'
else:
    second_revert_note = 'Revision 30587594 has a revert edit summary and matching negative size change, but its diff still needs retrieval to verify the exact removal.'

def md_table(frame, columns, limit=8):
    view = frame[columns].head(limit).fillna('').astype(str)
    return '| ' + ' | '.join(columns) + ' |\\n| ' + ' | '.join(['---']*len(columns)) + ' |\\n' + '\\n'.join('| ' + ' | '.join(v.replace('|','\\\\|') for v in row) + ' |' for row in view.to_numpy())

registered = editor_types.loc[editor_types.editor_type.eq('Registered (positive user ID)'), 'share_pct'].iloc[0]
anonymous = editor_types.loc[editor_types.editor_type.eq('Anonymous (user ID 0)'), 'share_pct'].iloc[0]
median_top10 = editor_metrics.top10_revision_share_pct.median()
largest_growth = growth.iloc[0]
context_note = 'No selected spike has an independently sourced contextual note in the review table.'
context_rows = context[context.source_url.notna() & context.source_url.ne('')]
if not context_rows.empty:
    row = context_rows.iloc[0]
    context_note = f\"For {row.article_title} in {str(row.timestamp)[:7]}, an external historical timeline documents contemporaneous events. This supports temporal context only and does not show those events caused editing activity. Source: [{row.source_title}]({row.source_url}).\"

report = f'''# Wikipedia Digital Archaeology Project — Analysis Report Draft

## Objective and Motivation

This project examines how Wikipedia articles about selected historical events evolve in the collected revision record. It asks when editing activity changes, how article size changes, how contributor activity is distributed, and whether editing patterns differ across event categories. Revision counts and byte sizes are observable traces of editorial activity; on their own, they do not establish the accuracy, completeness, or historical importance of the resulting content.

## Data and Data Collection

The analysis uses `historical_analysis/cleaned/historical_revisions_cleaned.csv`, a cleaned metadata file with {int(summary.revision_records):,} revision records and {int(summary.articles)} articles. Valid timestamps span {summary.earliest_timestamp_utc} to {summary.latest_timestamp_utc}, approximately {summary.coverage_days/365.2425:.1f} years. The data includes article title, revision and parent IDs, timestamp, username and user ID, edit summary, article size, and a minor-edit flag. It does not include the full text of each revision. The project collection scripts and sampling settings should be checked before describing this file as a complete revision history.

The average article has {summary.mean_revisions_per_article:,.1f} collected records and the median has {summary.median_revisions_per_article:,.0f}. The largest record counts are concentrated in a few pages:

{md_table(coverage, ['article_title','revisions','share_of_records_pct'], 6)}

The five largest pages by record count contribute {coverage.head(5).share_of_records_pct.sum():.1f}% of the dataset. This uneven coverage matters when interpreting pooled activity: totals reflect both article attention and the choice of articles in the project.

## Data Processing and Quality

Timestamps were parsed as UTC, identifiers and sizes coerced to numeric values, blank usernames treated as unavailable, and records sorted by article, timestamp, and revision ID before calculating consecutive observed size changes. No duplicate revision IDs, missing revision IDs, missing timestamps, negative sizes, or out-of-order input rows were found in the validation pass. Edit summaries were blank for {int(missing.loc[missing.field.eq('edit_comment'),'missing_count'].iloc[0]):,} records ({missing.loc[missing.field.eq('edit_comment'),'missing_percent'].iloc[0]:.1f}%). Other required fields in the table below had no missing values.

Parent-link checks found {int(parents.parent_not_in_collected_dataset)} parent IDs absent from the collected dataset and {int(parents.parent_timestamp_not_earlier_than_child)} records whose parent timestamp is equal to or later than the child timestamp. These rows are preserved in `step01_parent_link_anomalies.csv` for inspection. Some absent parents may reflect collection boundaries, but the non-earlier timestamps warrant checking against the source history before making fine-grained temporal claims. The largest observed article sizes are also exported because a small number exceed 1 MB; size-based outliers were not silently removed.

## Methods

Monthly and annual revision counts were calculated by article and across the full collection. Monthly spike screening used an article-specific robust threshold: median plus three scaled median absolute deviations. Where the median absolute deviation is zero, the analysis falls back to the upper Tukey fence; when both measures indicate no variation, it flags no observations. This avoids labeling every above-median count as anomalous in sparse series. The resulting table is a screening tool, not a causal explanation.

Article growth compares the first and last observed sizes in the collected record. It reports absolute byte change and percentage change. Percentage change is especially sensitive when the first observed size is very small, so absolute change is presented alongside it. These are observed endpoints, not necessarily page creation and current size. Contributor type is proxied by user ID: zero is classified anonymous, positive values registered, and missing values unavailable. Top-contributor shares are based on usernames within each article; a username does not establish a person's identity. One primary historical-event category was assigned to each article and documented in `step06_article_category_mapping.csv`.

## Results

### Activity and editing spikes

The highest record count belongs to World War II ({coverage.iloc[0].revisions:,}), followed by September 11 attacks ({coverage.iloc[1].revisions:,}). That distinction is descriptive and does not mean these events are historically more important. The per-article month table identifies the following large candidate spikes:

{md_table(spikes, ['article_title','timestamp','revisions','article_median','robust_threshold'], 8)}

The Arab Spring page has a 2,050-record month in February 2011 against a per-month median of 16. An external 2011 timeline documents major contemporaneous Arab Spring developments, including Egypt's February transition. {context_note} Other spikes remain uninvestigated; the revision counts alone cannot identify anniversaries, media coverage, controversies, or other causes.

The record spans over 25 years, but the files do not provide article publication dates or an independently verified complete history for each page. Therefore, comparisons of first and last observed activity cannot determine whether interest peaks soon after an event or page publication. Further work should establish article creation dates and confirm collection coverage before making that comparison.

### Article size and growth

The largest net observed size increase is {largest_growth.article_title}: {largest_growth.net_change_bytes:,.0f} bytes, from {largest_growth.first_size_bytes:,.0f} to {largest_growth.last_size_bytes:,.0f} bytes. The next largest observed increases are summarized here:

{md_table(growth, ['article_title','first_size_bytes','last_size_bytes','net_change_bytes','growth_pct'], 6)}

Percentage gains for pages whose earliest collected size was only a few dozen or a few hundred bytes become extremely large. Those percentages should not be compared as if they measured substantive historical knowledge. The largest consecutive size changes in Step 3 include extreme values; their revision IDs are preserved in the candidate table, but a byte delta cannot say what material was added or removed.

### Contributor participation

Across all records, {registered:.1f}% have a positive user ID, {anonymous:.1f}% have user ID zero, and the small remainder have unavailable IDs. The median share of revisions attributed to the ten most frequent usernames is {median_top10:.1f}% across articles. This indicates a spread of contribution counts in aggregate, but it cannot identify who contributors are or why they edit. The cleaned `is_minor` column is `True` for all {int(summary.revision_records):,} rows; consequently every article's minor-edit percentage is 100%. This field has no variation and is not useful for comparing editing behavior until its provenance is verified.

### Event-category comparison

The category analysis compares medians and article counts because the category sizes range from two to ten articles and the article-level distributions are skewed. It is descriptive: category definitions are researcher-assigned, overlapping interpretations are possible, and several category medians are based on very small samples.

{md_table(category_summary, ['primary_category','articles','median_revisions_per_article','median_revisions_per_year','median_growth_pct'], 10)}

All categories also show a 100% median minor-edit rate because the input flag is constant. That apparent similarity is a data limitation rather than evidence that editing behavior is the same across event types.

### Significant revision events and content changes

Step 5 retrieved {int((diff_status.retrieval_status=='retrieved').sum())} of {len(diff_status)} selected parent/revision comparisons. Inspection confirms several non-substantive events. The Russian Revolution and World War I examples include large vandalism-like text insertions; the World War I page then shows one verified revert, a repeat insertion, and a second verified revert. The JFK and World War II examples also contain nonsensical or repetitive text. By contrast, the recent Vietnam War change adds maintenance templates, the Emancipation Proclamation example adds a bibliography entry, and the American Civil War example removes one casualty-list item. These diffs document edits, not the truth of the affected historical claims. Each row below preserves the revision IDs and a direct diff link for verification.

{md_table(case_studies, ['article_title','timestamp','revision_id','change_classification'], 11)}

The World War I sequence is especially informative as an editorial process example: revision 30587516 adds a large profane text block; revision 30587560 removes it about 36 seconds later; revision 30587586 adds it again about 27 seconds after that. {second_revert_note} The verified revisions document a vandalism/reversion cycle in the page history, not a change to historical documentation. See the associated links in `step05_revision_case_studies.csv`.

## Answers to the Research Questions

1. **How does coverage evolve?** The collected records show activity across a long period and substantial differences in record counts and observed page sizes. Completeness and page-creation dates are not established, so these results describe the dataset rather than all Wikipedia history.
2. **When do substantial changes occur?** Robust monthly outliers and large byte deltas identify candidate periods and revisions. They require diff inspection and independent contextual research before interpretation.
3. **Do spikes coincide with public attention?** One Arab Spring example is contemporaneous with independently documented 2011 events. No causal relationship is established; most candidate spikes still need investigation.
4. **What changes are made to historical information?** The retrieved sample includes references, maintenance templates, a list-item removal, and several vandalism/reversion events. The sample is too small to characterize all content changes or assess the historical claims themselves.
5. **Do patterns differ by event type?** The category table shows descriptive differences in medians, but small and uneven category samples, researcher-defined labels, and extreme articles limit generalization.

## Problems, Limitations, and Interpretation

The most important limitation is that this dataset is revision metadata, not the article text or full diff history. Revision count is not a direct measure of public attention, accuracy, quality, or historical importance. Size changes include references, markup, templates, and formatting. Parent-link anomalies and large size outliers need source-level validation. Contributor metadata supports only aggregate classifications. The constant minor-edit field should be traced to the cleaning or collection process. Category comparisons may change under a different mapping, and category groups contain few pages. External context is incomplete and should be linked to dated independent sources.

## Future Work

First, run the Step 5 retrieval cell where the Wikimedia API is reachable and document a small set of verified diffs across multiple articles. Second, audit the 84 non-earlier parent links, 23 parent IDs absent from the collected file, and large page-size outliers. Third, verify whether the collected revision record is complete or sampled and obtain page creation dates. Fourth, investigate the largest monthly spikes with dated external sources while separating coincidence from cause. Fifth, confirm why `is_minor` is constant and correct the source data if necessary. These actions would make a report about content evolution stronger than one based solely on activity counts.

## Team Contributions

[Add team members and verified contributions. This information was not present in the project files available for this analysis.]

## Repository

[Insert the final repository link.]
'''
(OUTPUT_DIR/'final_report_draft.md').write_text(report,encoding='utf-8')
print('Updated',OUTPUT_DIR/'final_report_draft.md','with',len(report.split()),'words')
""")

# MediaWiki's compare module is an action endpoint, not a query property.
step5_path = ROOT / "step05_significant_revisions.ipynb"
step5_doc = json.loads(step5_path.read_text(encoding="utf-8"))
for cell in step5_doc["cells"]:
    if cell["cell_type"] == "code":
        cell["source"] = [line.replace("'action':'query','prop':'compare'", "'action':'compare'") for line in cell["source"]]
step5_path.write_text(json.dumps(step5_doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# Retain the complete 2005 World War I spam/reversion sequence as a case study.
step5_doc = json.loads(step5_path.read_text(encoding="utf-8"))
for cell in step5_doc["cells"]:
    if cell["cell_type"] == "code" and "candidates['candidate_reason']=np.select" in "".join(cell["source"]):
        source = "".join(cell["source"])
        source = source.replace("\ncols=['article_title'", "\nsequence_ids=[30587516,30587560,30587586,30587594]\nsequence_rows=df[df.revision_id.isin(sequence_ids)].copy()\ncandidates=pd.concat([candidates,sequence_rows]).drop_duplicates('revision_id',keep='first')\ncandidates.loc[candidates.revision_id.isin(sequence_ids),'candidate_reason']='World War I suspected spam/reversion sequence; inspect paired diffs'\ncols=['article_title'", 1)
        cell["source"] = source.splitlines(keepends=True)
    elif cell["cell_type"] == "code" and "for row in candidates.head(8).itertuples():" in "".join(cell["source"]):
        source = "".join(cell["source"])
        source = source.replace("for row in candidates.head(8).itertuples():", "sequence_sample=candidates[candidates.revision_id.isin(sequence_ids)]\nother_sample=candidates[~candidates.revision_id.isin(sequence_ids)].head(8)\ndiff_sample=pd.concat([sequence_sample,other_sample]).drop_duplicates('revision_id')\nfor row in diff_sample.itertuples():", 1)
        cell["source"] = source.splitlines(keepends=True)

append_source = """# Preserve added/deleted direction and direct diff links in the case-study evidence.
import re, html
from urllib.parse import quote
def diff_lines(markup, kind):
    blocks = re.findall(r'<td[^>]*diff-' + kind + r'[^>]*>(.*?)</td>', str(markup), flags=re.S)
    clean = []
    for block in blocks:
        block = re.sub(r'<br\\s*/?>', ' ', block, flags=re.I)
        clean.append(html.unescape(re.sub(r'<[^>]+>', '', block)).strip())
    return ' | '.join(x for x in clean if x)
examples = diffs.copy()
def useful_excerpt(s):
    s=str(s); low=s.lower()
    markers=['you are really fat','fuck!!!','bsadf82q','aaaaaaaaaaaaaaaa','sadfsadf']
    for marker in markers:
        pos=low.find(marker)
        if pos >= 0: return s[max(0,pos-160):pos+1000]
    return s[:700] + (' ... [middle omitted] ... ' + s[-700:] if len(s)>1500 else '')
examples['added_excerpt'] = examples.diff_html.map(lambda s: useful_excerpt(diff_lines(s,'addedline')))
examples['removed_excerpt'] = examples.diff_html.map(lambda s: useful_excerpt(diff_lines(s,'deletedline')))
examples['diff_url'] = examples.apply(lambda r: 'https://en.wikipedia.org/w/index.php?title='+quote(r.article_title.replace(' ','_'))+'&diff='+str(int(r.revision_id))+'&oldid='+str(int(r.parent_id)),axis=1)
def classify_diff(r):
    added=(r.added_excerpt or '').lower(); removed=(r.removed_excerpt or '').lower(); summary_text=(r.edit_comment or '').lower()
    markup=str(r.diff_html).lower()
    spam_markers=['fuck!!!','you are really fat','aaaaaaaaaaaaaaaa','bsadf82q','sadfsadf']
    if 'revert' in summary_text or 'undo' in summary_text or 'rollback' in summary_text:
        if any(x in removed for x in spam_markers) and not any(x in added for x in spam_markers): return 'Verified reversion removing spam-like text'
        return 'Reversion candidate; paired diff removes/changes prior content'
    if any(x in markup for x in spam_markers):
        return 'Vandalism/spam-like text removed' if any(x in removed for x in spam_markers) else 'Vandalism/spam-like text added; not historical content'
    if 'missing information' in added or '{{very long' in added: return 'Maintenance-template addition; flags coverage/length, does not add historical prose'
    if 'encyclopedia' in added or 'journal' in added or 'online]' in added: return 'Reference or bibliography addition; source quality needs review'
    if removed and not added: return 'Text removed; factual reason requires source verification'
    if added or removed: return 'Text or list changed; interpretation requires line-by-line review'
    return 'No changed line text extracted; inspect the linked diff'
examples['change_classification'] = examples.apply(classify_diff,axis=1)
examples['reviewer_notes'] = examples.change_classification
save_table(examples.drop(columns='diff_html'),'step05_revision_case_studies.csv')
display(examples[['article_title','timestamp','revision_id','parent_id','size_change_bytes','change_classification','added_excerpt','removed_excerpt','diff_url']])
"""
append_code(step5_path, append_source)

append_code(step5_path, """# Fetch the follow-up revisions to verify the suspected rapid World War I reverts.
sequence_ids=[30587560,30587586,30587594]
sequence_rows=df[df.revision_id.isin(sequence_ids)].copy()
sequence_rows['candidate_reason']='World War I suspected spam/reversion sequence; paired with 30587516'
candidates=pd.concat([candidates,sequence_rows]).drop_duplicates('revision_id',keep='first')
save_table(candidates[['article_title','timestamp','revision_id','parent_id','username','edit_comment','article_size_bytes','size_change_bytes','candidate_reason']], 'step05_significant_revision_candidates.csv')
extra=[]
for row in sequence_rows.itertuples():
    rec={'article_title':row.article_title,'timestamp':str(row.timestamp),'revision_id':int(row.revision_id),'parent_id':int(row.parent_id),'edit_comment':row.edit_comment,'size_change_bytes':row.size_change_bytes,'retrieval_status':'not attempted','diff_html':''}
    try:
        response=requests.get(API,params={'action':'compare','fromrev':rec['parent_id'],'torev':rec['revision_id'],'format':'json','formatversion':2},headers={'User-Agent':'WikipediaDigitalArchaeologyResearch/1.0 (educational analysis)'},timeout=5)
        response.raise_for_status(); payload=response.json(); comp=payload.get('compare',{})
        if comp.get('body') is not None: rec['diff_html']=comp['body']; rec['retrieval_status']='retrieved'
        else: rec['retrieval_status']='API returned no diff: '+str(payload.get('errors',payload))[:400]
    except Exception as exc: rec['retrieval_status']=f'retrieval failed: {type(exc).__name__}: {exc}'
    extra.append(rec)
diffs=pd.concat([diffs,pd.DataFrame(extra)]).drop_duplicates('revision_id',keep='last')
save_table(diffs,'step05_revision_diffs_raw.csv')
examples=diffs.copy()
examples['added_excerpt']=examples.diff_html.map(lambda s: diff_lines(s,'addedline')).str.slice(0,1400)
examples['removed_excerpt']=examples.diff_html.map(lambda s: diff_lines(s,'deletedline')).str.slice(0,1400)
examples['diff_url']=examples.apply(lambda r:'https://en.wikipedia.org/w/index.php?title='+quote(r.article_title.replace(' ','_'))+'&diff='+str(int(r.revision_id))+'&oldid='+str(int(r.parent_id)),axis=1)
examples['change_classification']=examples.apply(classify_diff,axis=1)
examples['reviewer_notes']=examples.change_classification
save_table(examples.drop(columns='diff_html'),'step05_revision_case_studies.csv')
display(examples[['article_title','timestamp','revision_id','parent_id','change_classification','added_excerpt','removed_excerpt','diff_url']])
""")
step5_doc = json.loads(step5_path.read_text(encoding="utf-8"))
for cell in step5_doc["cells"]:
    if cell["cell_type"] == "code":
        cell["source"] = [line.replace("time.sleep(.15)", "time.sleep(1.0)").replace("extra.append(rec)", "extra.append(rec); time.sleep(1.0)") for line in cell["source"]]
step5_path.write_text(json.dumps(step5_doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

step7_path = ROOT / "step07_synthesis.ipynb"
step7_doc = json.loads(step7_path.read_text(encoding="utf-8"))
for cell in step7_doc["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])
        source = source.replace("Detailed claims about added/removed historical information require successful Step 5 revision diff retrieval and human inspection; metadata alone cannot answer this question.", "The retrieved sample shows a vandalism/reversion cycle, maintenance-template edits, a bibliography addition, and a casualty-list removal; the small sample cannot characterize all revisions or verify historical claims.")
        source = source.replace("Only after inspecting retrieved before-and-after diffs; edit summaries and byte deltas are insufficient.", "The selected diff sample documents vandalism/reversion, maintenance templates, references, and a list-item removal; it is too small to characterize all content changes.")
        cell["source"] = source.splitlines(keepends=True)
step7_path.write_text(json.dumps(step7_doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
append_code(step7_path, """for index,(label,text) in enumerate(findings):
    if label == 'Content changes':
        findings[index] = (label,'The retrieved sample documents vandalism/reversion, maintenance-template edits, a bibliography addition, and a list-item removal; it is too small to characterize all content changes or verify historical claims.')
questions.loc[questions.research_question.eq('What kinds of changes are made to historical information?'),'answer']='The sample diff review documents vandalism/reversion, maintenance templates, a bibliography addition, and a casualty-list removal; it cannot characterize all changes or establish the correctness of claims.'
questions.loc[questions.research_question.eq('What kinds of changes are made to historical information?'),'confidence']='Observed in selected diffs; limited sample'
save_table(questions,'step07_research_question_answers.csv')
(OUTPUT_DIR/'step07_findings_summary.md').write_text('# Findings summary\\n\\n'+'\\n'.join(f'## {label}\\n\\n{text}\\n' for label,text in findings)+'\\n## Limitations\\n\\nRevision metadata does not encode all article text, explain editing motivation, or establish contributor identity. Contextual claims need independent dated sources. Categories are researcher-assigned.\\n',encoding='utf-8')
display(questions)
""")

